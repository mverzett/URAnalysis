'''
View to convert a 2D histogram into a 1D one
Author: M.Verzetti (U. Rochester)
'''

import array
import rootpy.plotting.views as views
import rootpy.plotting as plotting
import rootpy
try:
    from rootpy.utils import asrootpy
except ImportError:
    from rootpy import asrootpy
import ROOT
import os
from pdb import set_trace
from itertools import product
log = rootpy.log["/LinearizeView"]
ROOT.TH1.SetDefaultSumw2(True)

class LinearizeView(views._FolderView):
	def __init__(self, dir, overflow=False):
		self.oflow = overflow
		super(LinearizeView, self).__init__(dir)
		
	@staticmethod
	def linearize(histo, overflow=False):
		if histo.DIM != 2:
			raise RuntimeError('the histogram I got has dimension %d, which is not supported' % histogram.DIM)
		bx = histo.GetNbinsX()
		by = histo.GetNbinsY()
		nbins = (bx+2)*(by*2) if overflow else bx*by
		ret = plotting.Hist(nbins, 0, nbins)
		xran = range(0, bx+2) if overflow else range(1, bx+1)
		yran = range(0, by+2) if overflow else range(1, by+1)
		for idx, xy in enumerate(product(xran, yran)):
			x, y = xy
			ret[idx+1].value = histo[x,y].value
			ret[idx+1].error = histo[x,y].error
		ret.entries = histo.entries
		return ret

	def apply_view(self, obj):
		return LinearizeView.linearize(obj, self.oflow)
