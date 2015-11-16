'''

A rootpy histogram "view" which dusplays overflow bins

Author: Mauro Verzetti, University of Rochester

'''

from rootpy.plotting import views
try:
   from rootpy.utils import asrootpy
except ImportError:
   from rootpy import asrootpy
import rootpy.plotting as plt
from pdb import set_trace

class OverflowView(views._FolderView):
   def __init__(self, dir):
      super(OverflowView, self).__init__(dir)

   def apply_view(self, histo):
      ret = None
      dimensions = histo.get_dimension()
      if dimensions == 1:
         xbins = histo.get_nbins_x()
         edges = [histo.xaxis.get_bin_low_edge(i) for i in range(1, xbins+2)]
         lower_edge = edges[0] - histo.xaxis.get_bin_width(1)
         upped_edge = edges[-1] + histo.xaxis.get_bin_width(xbins)
         ret = plt.Hist([lower_edge]+edges+[upped_edge])
         ret.title = histo.title
         ret.decorate(**histo.decorators)
         ret.xaxis.title = histo.xaxis.title
         ret.yaxis.title = histo.yaxis.title
         for nbin, obin in zip(ret[1:-1], histo):
            nbin.value = obin.value
            nbin.error = obin.error
      elif dimensions == 2:
         xbins = histo.get_nbins_x()
         xedges = [histo.xaxis.get_bin_low_edge(i) for i in range(1, xbins+2)]
         lower_edge = xedges[0] - histo.xaxis.get_bin_width(1)
         upped_edge = xedges[-1] + histo.xaxis.get_bin_width(xbins)
         xedges = [lower_edge]+xedges+[upped_edge]

         ybins = histo.get_nbins_y()
         yedges = [histo.yaxis.get_bin_low_edge(i) for i in range(1, ybins+2)]
         lower_edge = yedges[0]  - histo.yaxis.get_bin_width(1)
         upped_edge = yedges[-1] + histo.yaxis.get_bin_width(ybins)
         yedges = [lower_edge]+yedges+[upped_edge]

         ret = plt.Hist2D(
            xedges,
            yedges,
            title = histo.title,
            **histo.decorators
            )
         ret.xaxis.title = histo.xaxis.title
         ret.yaxis.title = histo.yaxis.title
         for x_idx in range(1, xbins+1):
            for y_idx in range(1, ybins+1):               
               ret[x_idx+1, y_idx+1].value = histo[x_idx, y_idx].value
               ret[x_idx+1, y_idx+1].error = histo[x_idx, y_idx].error
      else:
         ret = histo
      return ret 
