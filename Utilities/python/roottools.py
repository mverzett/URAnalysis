'''
This module includes some root/rootpy tricks and helpful functions. It would be a good idea to port some of them to rootpy in the future
'''

import ROOT #should this be rootbindings?
import rootpy
import uuid
from pdb import set_trace

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

   def __contains__(self, key):
      pass

def ArgList(roolist):
   it = roolist.iterator()
   ret = []
   obj = it()
   while obj:
      ret.append(obj)
      obj = it()
   return ret

class Envelope(object):
   'represents an envelope of histograms'
   def __init__(self):
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

      self._hists = []
      self._nhists = 0
      self.median, self.one_sigma, self.two_sigma = None, None, None
      self.log = rootpy.log['/Envelope']

   def add(self, hist):
      self._hists.append(hist)
   
   def __iadd__(self, hist):
      self.add(hist)
      return self

   def _make_hists_(self):
      if self.median is not None:
         return
      self.median, self.one_sigma, self.two_sigma = tuple(self._hists[0].clone() for _ in range(3))
      self.median.reset()
      self.one_sigma.reset()
      self.two_sigma.reset()

      self.median.decorate(**self.styles['median'])
      self.one_sigma.decorate(**self.styles['one_sigma'])
      self.two_sigma.decorate(**self.styles['two_sigma'])
      
      self.median.title = 'median'
      self.one_sigma.title = '#pm1 #sigma'
      self.two_sigma.title = '#pm2 #sigma'

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

      nbins = len(self.median) 
      max_pos = self._nhists-1
      one_sigmas = ROOT.TMath.Nint(max_pos*0.158), ROOT.TMath.Nint(max_pos*(1-0.158))
      two_sigmas = ROOT.TMath.Nint(max_pos*0.022), ROOT.TMath.Nint(max_pos*(1-0.022))
      median     = ROOT.TMath.Nint(max_pos*0.5)
      for ibin in range(1, nbins+1):
         vals = [i.get_bin_content(ibin) for i in self._hists]
         vals.sort()
         self.median.SetBinContent(ibin, vals[median])
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

         self.one_sigma.SetBinContent(ibin, mean(*one_s_range))
         self.two_sigma.SetBinContent(ibin, mean(*two_s_range))
         
         self.one_sigma.SetBinError(ibin, delta(*one_s_range)/2.)
         self.two_sigma.SetBinError(ibin, delta(*two_s_range)/2.)

   def draw(self):
      self._compute_()
      self.two_sigma.Draw()
      self.one_sigma.Draw()
      self.median.Draw()

   def Draw(self):
      self.draw()

   def median(self, ibin):
      pass
   
   def one_sigma(self, ibin):
      pass
   
   def two_sigma(self, ibin):
      pass

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
