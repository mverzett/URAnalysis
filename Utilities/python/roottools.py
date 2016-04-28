'''
This module includes some root/rootpy tricks and helpful functions. It would be a good idea to port some of them to rootpy in the future
'''

import ROOT #should this be rootbindings?
import rootpy
import uuid
from pdb import set_trace
import URAnalysis.Utilities.prettyjson as prettyjson

def slice_hist(histo, ibin, axis='X'):
   '''cuts a slice of a Hist2D'''
   project = ''
   get_bin = None
   nbins   = -1
   if axis.upper() == 'X':
      project = 'projection_x'
      get_bin = lambda x: (x, ibin)
      nbins = histo.GetNbinsX()
   elif axis.upper() == 'Y':
      project = 'projection_y'
      get_bin = lambda x: (ibin, x)
      nbins = histo.GetNbinsY()
   else:
      raise ValueError('Allowed axis are X and Y, got %s' % axis)
   
   ret = getattr(histo, project)(
      uuid.uuid4().hex, 
      ibin, ibin
      )
   #do NOT trust error calculation in the slicing
   ret.Reset() 
   for idx in xrange(1, nbins+1):
      ret.SetBinContent(
         idx,
         histo.GetBinContent(*get_bin(idx))
         )
      ret.SetBinError(
         idx,
         histo.GetBinError(*get_bin(idx))
         )
   
   ret = rootpy.asrootpy(ret)
   ret.decorate(**histo.decorators)
   return ret

def spline2graph(spline):
   n_points = spline.GetNp()
   graph = rootpy.plotting.Graph(n_points)
   for idx in xrange(n_points):
      x, y = ROOT.Double(), ROOT.Double()
      spline.GetKnot(idx, x, y)
      graph.SetPoint(idx, x, y)
   return graph

class ArgSet(object):
   'a RooArgSet, but with python set functionalities'
   def __init__(self, rooset):
      self._rooset = rooset
      self._it = self._rooset.createIterator()
      self._obj = None

   def __iter__(self):
      #return self.ArgSetIt(self._rooset)
      it = self._rooset.createIterator()
      obj = it()
      while obj:
         yield obj
         obj = it.Next()         

   def __getitem__(self, val):
      for obj in self:
         if obj.GetName() == val:
            return obj
      raise KeyError(val)

   def __contains__(self, key):
      try:
         self[key]
         return True
      except KeyError:
         return False

   def keys(self):
      return set([i.GetName() for i in self])

def ArgList(roolist):
   it = roolist.iterator()
   ret = []
   obj = it()
   while obj:
      ret.append(obj)
      obj = it()
   return ret

class RealVar(ROOT.RooRealVar):
   #does it make sense/work?
   def __init__(self, val, err=None, name=None, range=None, asym_errs=None):
      if isinstance(val, ROOT.RooRealVar):
         super(RealVar, self).__init__(val)
         return
      vname = uuid.uuid4().hex if not name else name
      super(RealVar, self).__init__(vname, vname, val)
      if err is not None:
         self.error=err
      if range is not None:
         self.setRange(*range)
      if asym_errs is not None:
         self.setAsymError(*asym_errs)

   def __repr__(self):
      if self.hasAsymError():
         lo, hi = self.asym_error
         return "<%s | %s: %f %f/+%f>" % (
            self.__class__.__name__, self.name, self.value, lo, hi)
      elif self.hasError():
         return "<%s | %s: %f +/- %f>" % (
            self.__class__.__name__, self.name, self.value, self.error)         
      else:
         return "<%s | %s: %f>" % (
            self.__class__.__name__, self.name, self.value)         
   
   @property
   def name(self):
      return self.GetName()

   @name.setter
   def name(self, val):
      self.SetName(val)

   @property
   def value(self):
      return self.getVal()

   @value.setter
   def value(self, val):
      self.setVal(val)

   @property
   def error(self):
      if self.hasAsymError():
         return max(self.getErrorHi(), self.getErrorLo())
      else:
         return self.getError()

   @error.setter
   def error(self, val):
      self.setError(val)
   
   @property
   def asym_error(self):
      return self.getErrorLo(), self.getErrorHi()

   @asym_error.setter
   def asym_error(self, val):
      self.setAsymError(*val)
      

class Envelope(object):
   'represents an envelope of histograms'

   class BinProxy(object):
      'represents one bin of the envelope'
      def __init__(self, envelope, ibin):
         self.env_ = envelope
         self.ibin_ = ibin

      @property
      def median(self):
         return self.env_.median_value(self.ibin_)

      @property
      def one_sigma(self):
         return self.env_.one_sigma_range(self.ibin_)

      @property
      def two_sigma(self):
         return self.env_.two_sigma_range(self.ibin_)

      @property
      def error(self):
         center = self.median
         down, up = self.one_sigma
         return abs(down-center), abs(up-center)

   def __init__(self, mode='median'):
      self.styles = {
         'two_sigma' : {
            'legendstyle' : 'f',
            'drawstyle' : 'e2',
            'markerstyle' : 0,
            'fillcolor' : 'yellow',
            'linecolor' : 'yellow',
            'fillstyle': 'solid',
            },
         'one_sigma' : {
            'legendstyle' : 'f',
            'drawstyle' : 'e2 same',
            'markerstyle' : 0,
            'linecolor' : 'green',
            'fillcolor' : 'green',
            'fillstyle': 'solid',
            },
         'median' : {
            'legendstyle' : 'l',
            'drawstyle' : 'hist same',
            'linecolor' : 'red',
            'fillcolor' : 'green',
            'fillstyle': 'hollow',
            }
         }

      self.mode = mode
      self._hists = []
      self._nhists = 0
      self.median_, self.one_sigma_, self.two_sigma_ = None, None, None
      self.log = rootpy.log['/Envelope']

   def add(self, hist):
      self._hists.append(hist)
   
   def __iadd__(self, hist):
      self.add(hist)
      return self

   def _make_hists_(self):
      if self.median_ is not None:
         return
      self.median_, self.one_sigma_, self.two_sigma_ = tuple(self._hists[0].clone() for _ in range(3))
      self.median_.reset()
      self.one_sigma_.reset()
      self.two_sigma_.reset()

      self.median_.decorate(**self.styles['median'])
      self.one_sigma_.decorate(**self.styles['one_sigma'])
      self.two_sigma_.decorate(**self.styles['two_sigma'])
      
      self.median_.title = 'median'
      self.one_sigma_.title = '#pm1 #sigma'
      self.two_sigma_.title = '#pm2 #sigma'

   def _compute_(self):
      'compute the envelope'
      if len(self._hists) == self._nhists:
         return
      
      def mean(*args):
         return sum(args)/len(args)

      def delta(a1, a2):
         return abs(a1 - a2)

      self._nhists = len(self._hists)
      self._make_hists_()

      nbins = len(self.median_) 
      max_pos = self._nhists-1
      one_sigmas = ROOT.TMath.Nint(max_pos*0.158), ROOT.TMath.Nint(max_pos*(1-0.158))
      two_sigmas = ROOT.TMath.Nint(max_pos*0.022), ROOT.TMath.Nint(max_pos*(1-0.022))
      median     = ROOT.TMath.Nint(max_pos*0.5)
      for ibin in range(1, nbins+1):
         vals = [i.get_bin_content(ibin) for i in self._hists]
         vals.sort()
         med_val = vals[median] if self.mode == 'median' else sum(vals)/len(vals)
         self.median_.set_bin_content(ibin, med_val)
         one_s_range = tuple(vals[i] for i in one_sigmas)
         two_s_range = tuple(vals[i] for i in two_sigmas)
         self.log.debug(
            "bin %i: median: %.2f +/- %.2f, %.2f" % \
               (ibin, vals[median], one_s_range[0], one_s_range[1])
            )
         self.log.debug(
            "bin %i one sigma interval: mean %.2f, delta %.2f" % \
               (ibin, mean(*one_s_range), delta(*one_s_range)/2.)
            )

         self.one_sigma_.SetBinContent(ibin, mean(*one_s_range))
         self.two_sigma_.SetBinContent(ibin, mean(*two_s_range))
         
         self.one_sigma_.SetBinError(ibin, delta(*one_s_range)/2.)
         self.two_sigma_.SetBinError(ibin, delta(*two_s_range)/2.)

   def draw(self, options=''):
      self._compute_()
      self.two_sigma_.Draw(options)
      self.one_sigma_.Draw(options)
      self.median_.Draw(options)

   def Draw(self, options=''):
      self.draw()

   def __iter__(self):
      self._compute_()
      for i in range(self.nbins+2):
         yield Envelope.BinProxy(self, i)

   @property
   def median(self):
      self._compute_()
      return self.median_
   
   @property
   def one_sigma(self):
      self._compute_()
      return self.one_sigma_

   @property
   def two_sigma(self):
      self._compute_()
      return self.two_sigma_

   def median_value(self, ibin):
      self._compute_()
      return self.median_[ibin].value
   
   def one_sigma_range(self, ibin):
      self._compute_()
      center = self.one_sigma_[ibin].value
      err    = self.one_sigma_[ibin].error
      return center - err, center + err
   
   def two_sigma_range(self, ibin):
      self._compute_()
      center = self.two_sigma_[ibin].value
      err    = self.two_sigma_[ibin].error
      return center - err, center + err

   @property
   def nbins(self):
      self._compute_()
      return self.median_.GetNbinsX()

   def json(self):
      self._compute_()
      jret = []
      for idx in xrange(1, self.nbins+1):
         jbin = {
            'median' : self.median_value(idx),
            'one_sigma' : {'range' : self.one_sigma_range(idx)},
            'two_sigma' : {'range' : self.two_sigma_range(idx)},
            'label' : self.median_.GetXaxis().GetBinLabel(idx),
            'low_edge' : self.median_.GetXaxis().GetBinLowEdge(idx),
            'up_edge' : self.median_.GetXaxis().GetBinUpEdge(idx),
            }

         jbin['one_sigma']['val'] = max(
            abs(i - jbin['median']) 
            for i in jbin['one_sigma']['range']
            )
         jbin['two_sigma']['val'] = max(
            abs(i - jbin['median']) 
            for i in jbin['two_sigma']['range']
            )

         if jbin['median']:
            jbin['one_sigma']['relative'] = jbin['one_sigma']['val']/jbin['median']
            jbin['two_sigma']['relative'] = jbin['two_sigma']['val']/jbin['median']
         else:
            jbin['one_sigma']['relative'] = 0
            jbin['two_sigma']['relative'] = 0
         jret.append(jbin)
      return prettyjson.dumps(jret)

## def asrpy_plus(obj):
##    'extend asrootpy with custom classes and more'
##    #for some reason rootpy does not extend tgraphs
##    if obj.InheritsFrom('TGraphErrors'):
##       pass
##    elif obj.InheritsFrom('TGraph'):
##       ret = rootpy.plotting.Graph(obj.GetN())
##       for i in xrange(obj.GetN()):
##          ret.SetPoint(i, obj.GetX()[i], obj.GetY()[i])
##       return ret
##    elif obj.InheritsFrom('RooArgSet'):
##       return ArgSet(obj)
##    else:
##       return rootpy.asrootpy(obj)
