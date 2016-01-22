import os
import rootpy.io as io
from URAnalysis.Utilities.struct import Struct
from URAnalysis.Utilities.tables import Table
import URAnalysis.Utilities.prettyjson as prettyjson
import math
import re
from pdb import set_trace
import logging

from optparse import OptionParser
try:
   from HiggsAnalysis.CombinedLimit.DatacardParser import addDatacardParserOptions, parseCard
except ImportError:
   def addDatacardParserOptions(*args, **kwargs):
      raise RuntimeError("It was impossible to import HiggsAnalysis.CombinedLimit.DatacardParser,\n\n please move to CMSSW_7_1_5 and install the HiggsAnalysis-CombinedLimit package")
   def parseCard(*args, **kwargs):
      raise RuntimeError("It was impossible to import HiggsAnalysis.CombinedLimit.DatacardParser,\n\n please move to CMSSW_7_1_5 and install the HiggsAnalysis-CombinedLimit package")

def load(path):
   """Loads a HiggsAnalysis.CombinedLimit.DataCard from the path of a txt file
   This is NOT the same as URA.Utilities.Datacard (the class defined in this same package)
   This one is the one used by the fit, the URA one is used to write the txt file only.
   They share the same package because of the obvious link they share"""
   dummy = OptionParser()
   addDatacardParserOptions(dummy)
   opts, args = dummy.parse_args(['--X-allow-no-background'])

   card = None
   with open(path) as txt:
      card = parseCard(txt, opts)
   return card


class Systematic(object):
   'Interface to systematics to be profiled in the fit'
   def __init__(self, stype, val=None, unc=None):
      '''__init__(self, stype, val=None, unc=None): stype is how it will be 
      treated by the fit lnN, shape etc.. val and unc are used for
      param type sytematics'''
      self.type = stype
      self.applies_ = []
      if ((val is not None) or (unc is not None)) and stype != 'param':
         raise ValueError(
            'systematic value and uncertainty can '
            'only be assigned to param type systematics')
      if stype == 'param' and (val is None or unc is None):
         raise ValueError(
            'param type systematics require the definition'
            ' of acentral value and an uncertainty'
            )
      self.val = val
      self.unc = unc
      
   
   def applies(self, category, sample, value):
      '''applies(self, category, sample, value): defines how 
      a systematic behaves on a sample, POSIX regex are allowed'''
      self.applies_.append((re.compile(category), re.compile(sample), value))

   def effect(self, category, sample):
      '''effect(self, category, sample) returns the 
      effect on given sample''' 
      for cpat, spat, value in self.applies_:
         if cpat.match(category) and spat.match(sample):
            logging.debug('applying %.3f sys effect to %s/%s' % (value, category, sample))
            return '%.3f' % value
      return '-'

class DataCard(object):
   '''Handles HiggsAnalysis/CombinedLimit datacard formatting'''
   def __init__(self, signals):
      self.categories = {}
      self.systematics = {}
      if isinstance(signals, basestring):
         self.signals = [re.compile(signals)]
      else:
         self.signals = [re.compile(i) for i in signals]
      self.shape_sys_naming = re.compile(r'.*_.*(:?Down|Up)')
      self.yields = {}

   def add_category(self, name):
      'adds a category'
      self.categories[name] = Struct()
   
   def __getattr__(self, val):
      'access categories with dot operator'
      if val in self.categories:
         return self.categories[val]
      else:
         return super(DataCard, self).__getattr__(val)

   def __getitem__(self, name):
      'x.__getitem__(i, y) <==> x[i]'
      return self.categories[name]

   def __setitem__(self, name, val):
      'DEPRECATED! x.__setitem__(i, y) <==> x[i]=y'
      self.categories[name] = val

   @staticmethod
   def remove_negative_bins(histo, keep_integral=True):
      ret = histo.Clone()
      integral = histo.Integral()
      for bin in ret:
         if bin.value < 0:
            bin.value = 0
            bin.error = 0
      
      if keep_integral and integral:
         new_integral = ret.Integral()
         ret.Scale(integral/new_integral if new_integral else 0.)
      return ret

   def normalize_signals(self):
      for cname, content in self.categories.iteritems():
         for sample, histo in content.iteritems():
            if any(j.match(sample) for j in self.signals): #if is signal
               #check if the category already exists
               if cname not in self.yields:
                  self.yields[cname] = {}
               
               #check if sample already exists: in this case ignore
               #this prevents screwing up the yields in case this 
               #function is called multiple times.
               if sample in self.yields[cname]:
                  continue

               #store integral an then normalize
               self.yields[cname][sample] = histo.Integral()
               if self.yields[cname][sample]:                  
                  histo.Scale(1./self.yields[cname][sample])
               else:
                  logging.warning('No yield for %s in %s, skipping...' % (sample, cname))

   def save(self, filename, directory=''):
      'save(self, name, directory='') saves the datacard and the shape file'
      ##
      # Write datacard file
      ##
      txt_name = os.path.join(directory, '%s.txt' % filename)
      with open(txt_name, 'w') as txt:
         separator = '-'*40+'\n'
         ncategories = len(self.categories)
         sample_category = self.categories.values()[0]
         has_data = 'data_obs' in sample_category
         samples  = sample_category.keys()
         samples  = filter(lambda x: not self.shape_sys_naming.match(x), samples)
         #set_trace()
         nsamples = len(samples)
         if has_data:
            nsamples -= 1
         #HEADER
         txt.write('imax    %i     number of categories \n' % ncategories)
         txt.write('jmax    %i     number of samples minus one \n' % (nsamples-1))
         txt.write('kmax    *     number of nuisance parameters \n')
         #WHERE TO FIND THE SHAPES
         txt.write(separator)
         txt.write('shapes * * %s.root $CHANNEL/$PROCESS $CHANNEL/$PROCESS_$SYSTEMATIC \n' % filename)
         #DATA COUNT IN EACH CATEGORY (FIXME: ASSUMES YOU HAVE DATA)
         txt.write(separator)
         max_cat_name = max(max(len(i) for i in self.categories), 11)+4
         format = (''.join(['%-', str(max_cat_name), 's']))*(ncategories+1)+'\n'
         txt.write(format % tuple(['bin']+self.categories.keys()))
         txt.write(format % tuple(['observation']+['%-7.1f' % i.data_obs.Integral() for i in self.categories.itervalues()]))
         #SAMPLES TABLE
         mcsamples = []
         bkg_idx, sig_idx = 1, 0
         for sample in samples:
            if 'data_obs' == sample:
               continue
            if any(j.match(sample) for j in self.signals):
               mcsamples.append((sample, sig_idx))
               sig_idx -= 1
            else:
               mcsamples.append((sample, bkg_idx))
               bkg_idx += 1
         mcsamples = dict(mcsamples)

         #WRITE RATE FOR EACH SAMPLE/CATEGORY
         columns = ['header:%-30s']
         bin_line = ['bin']
         proc_num_line = ['process']
         proc_name_line = ['process']
         rate_line = ['rate']
         for category, info in self.categories.iteritems():
            category_yield = 0
            for sample, shape in info.iteritems():
               if sample not in mcsamples: continue
               width = max(len(category), len(sample), 7)+4
               format = ''.join(['%-', str(width), 's'])
               columns.append('%s_%s:%s' % (category, sample, format)) 
               bin_line.append(category)
               proc_num_line.append(mcsamples[sample])
               proc_name_line.append(sample)
               rate = shape.Integral()
               #keep the first 6 significant digits
               if rate <= 0:
                  logging.error(
                     'Sample %s in category %s has a negative'
                     ' number of expected events! (%f) \n'
                     'Clamping to zero' % (sample, category, rate)
                     )
                  shape.Reset()
                  rate = 0.
                  #raise ValueError(
                  #   'Sample %s in category %s has a negative'
                  #   ' number of expected events! (%f)' % (sample, category, rate)
                  #   )
               category_yield += rate
               mag  = max(int(math.log10(abs(rate))), 0) if rate != 0 else 0
               float_format = '%.'+str(max(5-mag,0))+'f'
               rate_line.append(float_format % rate)
            if rate == 0:
               logging.warning("Category %s does not have any expected event!" % category)

         #SYSTEMATICS TABLE
         sys_table = Table(*columns, show_title=False, show_header=False)
         sys_table.add_separator()
         sys_table.add_line(*bin_line)
         sys_table.add_line(*proc_num_line)
         sys_table.add_line(*proc_name_line)
         sys_table.add_line(*rate_line)
         sys_table.add_separator()
         param_sys = []
         line = None
         for sys_name, syst in self.systematics.iteritems():
            if syst.type == 'param':
               param_sys.append((sys_name, syst))
               continue
            line = sys_table.new_line()
            line.header = '%s %s' % (sys_name, syst.type)
            logging.debug('Adding systematic %s' % sys_name)
            for category, info in self.categories.iteritems():
               for sample, _ in info.iteritems():
                  if sample not in mcsamples: continue
                  line['%s_%s' % (category, sample)] = syst.effect(category, sample)
         if line is not None: del line
         sys_table.add_separator()
         txt.write('%s\n' % sys_table)
         for sys_name, syst in param_sys:
            txt.write('%s  param %f %f\n' % (sys_name, syst.val, syst.unc))
      logging.info('Written file %s' % txt_name)
      ##
      # Write shape file
      ##
      shape_name = os.path.join(directory, '%s.root' % filename)
      with io.root_open(shape_name, 'recreate') as out:
         for name, cat in self.categories.iteritems():
            out.mkdir(name).cd()
            for sample, shape in cat.iteritems():
               shape.SetName(sample)
               shape.SetTitle(sample)
               shape.Write()
      logging.info('Written file %s' % shape_name)
      ##
      # if we normalized the signal to outsource the yields to a json file
      # dump it too
      ##
      if self.yields:
         json_name = os.path.join(directory, '%s.json' % filename)
         with open(json_name, 'w') as txt:
            txt.write(prettyjson.dumps(self.yields))

   def add_systematic(self, name, stype, categories, samples, value, unc=None):
      'add a systematic effect to a bunch of samples. POSIX regex supported'
      if name not in self.systematics:
         if stype == 'param':
            self.systematics[name] = Systematic(stype, unc=unc, val=value)
         else:
            self.systematics[name] = Systematic(stype)
      if stype != self.systematics[name].type:
         raise ValueError(
            'MISMATCH! Systematic %s was defined as %s, but it'
            ' has been called as %s.' % (name, self.systematics[name].type, stype))
      self.systematics[name].applies(categories, samples, value)

   def add_bbb_systematics(self, categories, samples, threshold=0.05, relative=True):
      '''add_bbb_systematics(categories, samples, threshold=0.05, relative=True)
if relative is set to True (default) it checks that the error is >= threshold*content of data bin
otherwises uses the samples bin content
      '''
      if isinstance(categories, list):
         categories = [re.compile(i) for i in categories]
      elif isinstance(categories, basestring):
         categories = [re.compile(categories)]
      else:
         raise TypeError('categories can only be lists or strings')

      if isinstance(samples, list):
         samples = [re.compile(i) for i in samples]
      elif isinstance(samples, basestring):
         samples = [re.compile(samples)]
      else:
         raise TypeError('samples can only be lists or strings')

      sample_category = self.categories.values()[0]
      all_samples = sample_category.keys()
      all_samples = filter(lambda x: not self.shape_sys_naming.match(x) and x <> 'data_obs', all_samples)

      samples_to_process = filter(
         lambda x: any(i.match(x) for i in samples), 
         all_samples
         )
      categories_to_process = [
         i for i in self.categories
         if any(j.match(i) for j in categories)
         ]

      n_nuis=0
      for category in categories_to_process:
         for sample in samples_to_process:
            shape = self.categories[category][sample]
            if 'data_obs' not in self.categories[category]:
               raise RuntimeError(
                  'To use relative threshold (default) in '
                  'bin-by-bin error computation you must have '
                  'data_obs histogram available for '
                  'category: %s' % category
                  )
            reference = self.categories[category][sample] \
               if not relative else self.categories[category]['data_obs']
            nbins = shape.GetNbinsX()
            for idx in xrange(1, nbins+1):
               content = reference.GetBinContent(idx)
               error   = shape.GetBinError(idx)
               if not content or (error/content) < threshold:
                  continue
               n_nuis+=1
               unc_name = '%s_%s_bin_%i' % (category, sample, idx)
               for postfix, shift in zip(['Up', 'Down'], [error, -1*error]):
                  shifted = shape.Clone()
                  shifted.SetBinContent(idx, max(content+shift, 10**-5))
                  self.categories[category]['%s_%s%s' % (sample, unc_name, postfix)] = shifted
               self.add_systematic(unc_name, 'shape', category, sample, 1.00)
      logging.info(
         'Added %i BBB nuisances, in %i samples, in %i categories' % \
         (n_nuis, len(samples_to_process), len(categories_to_process))
         )
