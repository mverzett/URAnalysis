'''

Base class which makes nice plots.
Original Author: Evan K. Friis in FinalStateAnalysis
Many adaptation and import by Mauro Verzetti

'''

import fnmatch
import re
import os
import rootpy.plotting.views as views
import rootpy.plotting as plotting
import rootpy.io as io
from URAnalysis.PlotTools.data_views import data_views
from URAnalysis.PlotTools.data_styles import data_styles
from URAnalysis.PlotTools.views.RebinView import RebinView
from URAnalysis.Utilities.struct import Struct
import URAnalysis.Utilities.prettyjson as prettyjson
import sys
from rootpy.plotting.hist import HistStack
from pdb import set_trace
import logging
import ROOT
from BasePlotter import BasePlotter

ROOT.gROOT.SetBatch(True)

_original_draw = plotting.Legend.Draw
# Make legends not have crappy border
def _monkey_patch_legend_draw(self, *args, **kwargs):
	''' Make a plotting.legend look nice '''
	self.SetBorderSize(0)
	_original_draw(self, *args, **kwargs)
plotting.Legend.Draw = _monkey_patch_legend_draw

class Plotter(BasePlotter):
	def __init__(self, files, lumifiles, outputdir, 
				 styles=data_styles, blinder=None, forceLumi=-1, lumi_scaling=1.,
				 fileMapping=True):
		''' Initialize the Plotter object

		Files should be a list of SAMPLE_NAME.root files.
		Lumifiles should contain floats giving the effective luminosity of
		each of the files.

		If [blinder] is not None, it will be applied to the data view.
		'''
		super(Plotter, self).__init__(outputdir)
		self.views = data_views(files, lumifiles, styles, forceLumi, lumi_scaling)
		if blinder:
			# Keep the unblinded data around if desired.
			self.views['data']['unblinded_view'] = self.views['data']['view']
			# Apply a blinding function
			self.views['data']['view'] = blinder(self.views['data']['view'])
		self.data = self.views['data']['view'] if 'data' in self.views else None
		# List of MC sample names to use.  Can be overridden.
		self.mc_samples = [i for i in self.views if not i.startswith('data')]

		file_to_map = filter(lambda x: x.startswith('data_'), self.views.keys())
		if not file_to_map: #no data here!
			file_to_map = self.views.keys()[0]
		else:
			file_to_map = file_to_map[0]
		#set_trace()
		self.file_dir_structure = Plotter.map_dir_structure( self.views[file_to_map]['file'] )

	@staticmethod
	def map_dir_structure(directory, dirName=''):
		'''Maps the content of a TFile'''
		objects = [(i.GetName(), i.GetClassName()) for i in directory.GetListOfKeys()]
		#logging.debug('Entered dir %s, found %d objects' % (dirName, len(objects)))
		ret     = []
		for keyname, keyclass in objects:
			if keyclass.startswith('TDirectory'):
				subdirName = os.path.join(dirName,keyname)
				ret.append(subdirName)
				ret.extend(Plotter.map_dir_structure(directory.Get(keyname), subdirName))
		return ret


	@staticmethod
	def rebin_view(x, rebin):
		''' Make a view which rebins histograms '''
		output = RebinView(x, rebin)
		return output

	def get_view(self, sample_pattern, key_name='view'):
		''' Get a view which matches a pattern like "Zjets*"
		Multiple matches are summed together (e.g. "Z?jets*")

		Generally key_name does not need to be modified, unless getting
		unblinded data via "unblinded_view"
		'''
		matching = []
		samples  = []
		for sample, sample_info in self.views.iteritems():
			if fnmatch.fnmatch(sample, sample_pattern):
				try: 
					matching.append( sample_info[key_name] )
					samples.append(sample)
				except KeyError:
					raise KeyError("you asked for %s in sample %s, but it was not found, I only have: %s" % 
								   (key_name, sample, ','.join(sample_info.keys())))
		
		if matching:
			logging.debug("Merging %s into a single view. Asked: %s" % (' '.join(samples), sample_pattern) )
			return views.SumView(*matching)
		else:
			raise KeyError("I can't find a view that matches %s, I have: %s" % (
				sample_pattern, " ".join(self.views.keys())))

	def mc_views(self, rebin=1, preprocess=None, folder=''):
		''' return a list with all the mc samples views'''
		mc_views = []
		for x in self.mc_samples:
			mc_view = self.get_view(x)
			if preprocess:
				mc_view = preprocess(mc_view)
			if folder:
				mc_view = self.get_wild_dir(mc_view, folder)
			mc_views.append(
				self.rebin_view(mc_view, rebin)
				)
		return mc_views

	def make_stack(self, rebin=1, preprocess=None, folder='', sort=False, postprocess=None):
		''' Make a stack of the MC histograms '''
		mc_views =  self.mc_views(rebin, preprocess, folder)
		if postprocess:
			mc_views = [postprocess(i) for i in mc_views]
		return views.StackView(*mc_views, sorted=sort)

	def add_legend(self, samples, leftside=True, entries=None):
		''' Build a legend using samples.

		If entries is None it will be taken from len(samples)

		'''
		nentries = entries if entries is not None else len(samples)
		legend = None
		if leftside:
			legend = plotting.Legend(nentries, leftmargin=0.03, topmargin=0.05, rightmargin=0.65, entryheight=0.03)
		else:
			legend = plotting.Legend(nentries, rightmargin=0.07, topmargin=0.05, leftmargin=0.45, entryheight=0.03)
		for sample in samples:
			legend.AddEntry(sample)
			## if isinstance(sample, plotting.HistStack):
			##	 for s in sample:
			##         if getattr(sample, 'inlegend', True):
			##             label = s.GetTitle()
			##			 style = s.legendstyle
			##			 legend.AddEntry(s, style, label) 
			## else:
			##	 legend.AddEntry(sample)
		legend.SetEntrySeparation(0.0)
		legend.SetMargin(0.35)
		legend.Draw()
		self.keep.append(legend)
		return legend

	def add_ratio_plot(self, data_hist, *tests, **kwargs):
		'''Adds a ratio plot under the main pad, with same x range'''
		_, self.label_factor = self.dual_pad_format()
		self.lower_pad.cd()
		x_range = kwargs.get('x_range', None)
		xtitle  = kwargs.get('xtitle' , '')
		quote_errors= kwargs.get('quote_errors', False)

		test_hists = [
			sum(i.hists) if isinstance(i, HistStack) else i.Clone()
			for i in tests
			]
		if len(test_hists) > 1:
			for histo in test_hists:
				histo.markercolor = histo.fillcolor
		for i in test_hists:
			i.decorate(**data_hist.decorators)
		
		if len(test_hists) > 1:
			raise RuntimeError("add_ratio_plot works only for a single comparison (data/MC) for multiple ratios use compare or overlay_and_compare")
		
		self.compare(
			test_hists[0], [data_hist.Clone()], 'ratio', xtitle=xtitle, ytitle='Observed/MC'
			)

		if x_range is None:
			x_range = [data_hist[0].x.high, data_hist[-1].x.low]
		ref_function = ROOT.TF1('f', "1.", *x_range)
		ref_function.SetLineWidth(3)
		ref_function.SetLineStyle(2)
		ref_function.Draw('same')
		self.keep.append(ref_function)
		
		return None

	def fit_shape(self, histo, model, x_range, fitopt='IRMENS'):
		'''Performs a fit with ROOT libraries.
		Model is a tuple defining the function to be used and 
		gets parsed by Plotter.parse_formula'''
		tf1 = self.parse_formula(*model) 
		tf1.SetRange(*x_range)
		tf1.SetLineColor(ROOT.EColor.kAzure)
		tf1.SetLineWidth(3)
		result = histo.Fit(tf1, fitopt) #WL
		# "WL" Use Loglikelihood method and bin contents are not integer,
		#               i.e. histogram is weighted (must have Sumw2() set)
		# "Q"  Quiet mode (minimum printing)
		# "E"  Perform better Errors estimation using Minos technique
		# "M"  More. Improve fit results.
		#      It uses the IMPROVE command of TMinuit (see TMinuit::mnimpr).
		#      This algorithm attempts to improve the found local minimum by searching for a
		#      better one.
		# "R"  Use the Range specified in the function range
		# "N"  Do not store the graphics function, do not draw
		# "S"  The result of the fit is returned in the TFitResultPtr
		numpoints = tf1.GetNpx() #number of points in which the func is evaluated
		func_hist = plotting.Hist(numpoints, *x_range)
		(ROOT.TVirtualFitter.GetFitter()).GetConfidenceIntervals(func_hist)
		func_hist.linewidth = 0
		func_hist.fillcolor = ROOT.EColor.kAzure - 9
		func_hist.fillstyle = 3013
		func_hist.markersize = 0
		func_hist.Draw('same e3')
		tf1.Draw('same')
		self.keep.extend([
			tf1,
			func_hist
		])
		return tf1
		
	def plot(self, sample, path, drawopt='', rebin=None, styler=None, xaxis='', yaxis='', xrange=None):
		''' Plot a single histogram from a single sample.

		Returns a reference to the histogram.
		'''
		view = self.get_view(sample)
		if rebin:
			view = self.rebin_view(view, rebin)
		histo = view.Get(path)
		if xrange:
			histo.GetXaxis().SetRange(xrange[0], xrange[1])
		if styler:
			styler(histo)
		histo.xaxis.title = xaxis
		histo.yaxis.title = yaxis
		histo.drawstyle = drawopt
		#set_trace()
		histo.Draw(drawopt)
		self.keep.append(histo)
		return histo

	def compare_shapes(self, sample1, sample2, path, rebin=None):
		''' Compare the spectra from two different samples '''
		view1 = views.NormalizeView(self.views[sample1]['view'])
		if rebin:
			view1 = self.rebin_view(view1, rebin)
		histo1 = view1.Get(path)
		view2 = views.NormalizeView(self.views[sample2]['view'])
		if rebin:
			view2 = self.rebin_view(view2, rebin)
		histo2 = view2.Get(path)
		histo1.Draw('pe')
		histo2.SetMarkerColor(ROOT.EColor.kRed)
		histo2.Draw('pe,same')
		histo1.SetMaximum(
			1.2*max(histo1.GetMaximum(), histo2.GetMaximum()))
		self.keep.append( (histo1, histo2) )

	def expand_path(self, pattern):
		'''makes a regex out of a POSIX path, the correct way'''
		#because fnmatch does not treat / properly and may generate LOTS of problems
		if any((i in pattern) for i in ['*', '?']):
			repattern = re.compile('^'+pattern.replace('*','[^/]*').replace('?','[^/]')+'$')
			return [i for i in self.file_dir_structure if repattern.match(i)]
		else:
			return [pattern]

	def get_wild_dir(self, view, path):
		'''equivalent of SubdirectoryView, 
		but with unix-style wildcards'''
		paths = self.expand_path(path)
		return views.SumView(
			*[ views.SubdirectoryView(view, i) for i in paths]
			)

	def get_wild_path(self, view, path):
		'''gets a FULL path with wildcards in it. 
		By full it is intended till the histogram to be picked'''
		base_name = os.path.basename(path)
		dir_name  = os.path.dirname(path)
		return self.get_wild_dir(view, dir_name).Get(base_name)

	def plot_mc_vs_data(self, folder, variable, rebin=1, xaxis='',
						leftside=True, xrange=None, preprocess=None, postprocess=None,
						show_ratio=False, ratio_range=0.2, sort=False,
						logy=False, nodata=False):
		''' Compare Monte Carlo to data '''
		#path = os.path.join(folder, variable)
		labelSizeFactor1, labelSizeFactor2 = 1, 1
		if show_ratio:
			labelSizeFactor1, labelSizeFactor2 = self.dual_pad_format()
			self.label_factor = labelSizeFactor1
		mc_stack_view = self.make_stack(rebin, preprocess, folder, sort, postprocess=postprocess)
		mc_stack = mc_stack_view.Get(variable)
		self.style_histo(mc_stack)
		mc_stack.Draw()
		mc_stack.GetHistogram().GetYaxis().SetTitle('Events')
		mc_stack.GetHistogram().GetXaxis().SetTitle(xaxis)
		label_size = ROOT.gStyle.GetTitleSize()*self.label_factor
		mc_stack.GetHistogram().GetYaxis().SetLabelSize(label_size)  
		mc_stack.GetHistogram().GetXaxis().SetLabelSize(label_size)  
		mc_stack.Draw()
		if xrange:
			mc_stack.GetXaxis().SetRangeUser(xrange[0], xrange[1])
			mc_stack.Draw()
		self.keep.append(mc_stack)
		to_legend = [mc_stack]
		if 'data' in self.views and not nodata:
			# Draw data
			data_view = self.get_view('data')
			if preprocess:
				data_view = preprocess( data_view )
			data_view = self.get_wild_dir(
				self.rebin_view(data_view, rebin),
				folder
				)
			if postprocess:
				data_view = postprocess(data_view)
			data = data_view.Get(variable)
			self.keep.append(data)
			data.Draw('same')
			self.keep.append(data)
			to_legend.append(data)
			# Make sure we can see everything
			yrange = self._get_y_range_(data, mc_stack)
			mc_stack.SetMinimum(10**-3) #ignore minimum!
			mc_stack.SetMaximum(yrange[1])
		else:
			yrange = self._get_y_range_(mc_stack)
			mc_stack.SetMinimum(yrange[0])
			mc_stack.SetMaximum(yrange[1])
			logging.warning("No data found! Skipping drawing data...")
		# Add legend
		self.add_legend(to_legend, leftside, entries=len(mc_stack.GetHists())+len(to_legend)-1)
		if logy:
			self.pad.SetLogy()
		if show_ratio and not nodata and 'data' in self.views:
			self.label_factor = labelSizeFactor2
			for i in mc_stack.hists:
				i.xaxis.title=xaxis
			self.add_ratio_plot(data, mc_stack, x_range=xrange, ratio_range=ratio_range)
