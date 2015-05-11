import os
import rootpy.io as io
from URAnalysis.Utilities.struct import Struct
from URAnalysis.Utilities.tables import Table
import math
from fnmatch import fnmatch
from pdb import set_trace
import logging

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
      self.applies_.append((category, sample, value))

   def effect(self, category, sample):
      '''effect(self, category, sample) returns the 
      effect on given sample''' 
      for cpat, spat, value in self.applies_:
         if fnmatch(category, cpat) and fnmatch(sample, spat):
            return '%.3f' % value
      return '-'

class DataCard(object):
   '''Handles HiggsAnalysis/CombinedLimit datacard formatting'''
   def __init__(self, signals):
      self.categories = {}
      self.systematics = {}
      if isinstance(signals, basestring):
         self.signals = [signals]
      else:
         self.signals = signals
      
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

   def save(self, name, directory=''):
      'save(self, name, directory='') saves the datacard and the shape file'
      ##
      # Write datacard file
      ##
      txt_name = os.path.join(directory, '%s.txt' % name)
      with open(txt_name, 'w') as txt:
         separator = '-'*40+'\n'
         ncategories = len(self.categories)
         sample_category = self.categories.values()[0]
         has_data = 'data_obs' in sample_category
         samples  = sample_category.keys()
         samples  = filter(lambda x: not fnmatch(x, '*_*Up'), samples)
         samples  = filter(lambda x: not fnmatch(x, '*_*Down'), samples)
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
         txt.write('shapes * * %s.root $CHANNEL/$PROCESS $CHANNEL/$PROCESS_$SYSTEMATIC \n' % name)
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
            if any(fnmatch(sample, j) for j in self.signals):
               mcsamples.append((sample, sig_idx))
               sig_idx -= 1
            else:
               mcsamples.append((sample, bkg_idx))
               bkg_idx += 1
         mcsamples = dict(mcsamples)

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
               category_yield += rate
               #keep the first 6 significant digits
               mag  = max(int(math.log10(rate)), 0) if rate != 0 else 0
               float_format = '%.'+str(max(5-mag,0))+'f'
               rate_line.append(float_format % shape.Integral())
            if rate == 0:
               logging.warning("Category %s does not have any expected event!" % category)

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
            for category, info in self.categories.iteritems():
               for sample, _ in info.iteritems():
                  if sample not in mcsamples: continue
                  line['%s_%s' % (category, sample)] = syst.effect(category, sample)
         if line is not None: del line
         sys_table.add_separator()
         txt.write('%s\n' % sys_table)
         for sys_name, syst in param_sys:
            txt.write('%s  param %f %f' % (sys_name, syst.val, syst.unc))
      logging.info('Written file %s' % txt_name)
      ##
      # Write shape file
      ##
      shape_name = os.path.join(directory, '%s.root' % name)
      with io.root_open(shape_name, 'recreate') as out:
         for name, cat in self.categories.iteritems():
            out.mkdir(name).cd()
            for sample, shape in cat.iteritems():
               shape.SetName(sample)
               shape.Write()
      logging.info('Written file %s' % shape_name)

   def add_systematic(self, name, stype, categories, samples, value, unc=None):
      'add a systematic effect to a bunch of samples. POSIX regex supported'
      if name not in self.systematics:
         if stype == 'param':
            self.systematics[name] = Systematic(stype, unc, value)
         else:
            self.systematics[name] = Systematic(stype)
      if stype != self.systematics[name].type:
         raise ValueError(
            'MISMATCH! Systematic %s was defined as %s, but it'
            ' has been called as %s.' % (name, self.systematics[name].type, stype))
      self.systematics[name].applies(categories, samples, value)

   def add_bbb_systematics(self, categories, samples, threshold=0.05):
      sample_category = self.categories.values()[0]
      all_samples = sample_category.keys()
      all_samples = filter(lambda x: not fnmatch(x, '*_*Up'),   all_samples)
      all_samples = filter(lambda x: not fnmatch(x, '*_*Down'), all_samples)
      
      samples_to_process = filter(
         lambda x: any(fnmatch(x, i) for i in samples), 
         all_samples
         )
      categories_to_process = [
         i for i in self.categories
         if any(fnmatch(i, j) for j in categories)
         ]

      n_nuis=0
      for category in categories_to_process:
         for sample in samples_to_process:
            shape = self.categories[category][sample]
            nbins = shape.GetNbinsX()
            for idx in xrange(1, nbins+1):
               content = shape.GetBinContent(idx)
               error   = shape.GetBinError(idx)
               if not content or (error/content) < threshold:
                  continue
               n_nuis+=1
               unc_name = '%s_%s_bin_%i' % (category, sample, idx)
               for postfix, shift in zip(['Up', 'Down'], [error, -1*error]):
                  shifted = shape.Clone()
                  shifted.SetBinContent(idx, content+shift)
                  self.categories[category]['%s_%s%s' % (sample, unc_name, postfix)] = shifted
               self.add_systematic(unc_name, 'shape', category, sample, 1.00)
      logging.info(
         'Added %i BBB nuisances, in %i samples, in %i categories' % \
         (n_nuis, len(samples_to_process), len(categories_to_process))
         )