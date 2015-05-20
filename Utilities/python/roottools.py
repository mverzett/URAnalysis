'''
This module includes some root/rootpy tricks and helpful functions. It would be a good idea to port some of them to rootpy in the future
'''

import ROOT #should this be rootbindings?
import rootpy
import uuid

def slice_hist(histo, strt, end=None, axis='X'):
   '''cuts a slice of a Hist2D, if end is not 
   provided, is set to the start'''
   project = ''
   if axis.upper() == 'X':
      project = 'projection_x'
   elif axis.upper() == 'Y':
      project = 'projection_y'
   else:
      raise ValueError('Allowed axis are X and Y, got %s' % axis)
   
   ret = getattr(histo, project)(
      uuid.uuid4().hex, 
      strt, 
      strt if end is None else end
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
