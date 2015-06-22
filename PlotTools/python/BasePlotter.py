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

ROOT.gROOT.SetBatch(True)

_original_draw = plotting.Legend.Draw
# Make legends not have crappy border
def _monkey_patch_legend_draw(self, *args, **kwargs):
    ''' Make a plotting.legend look nice '''
    self.SetBorderSize(0)
    _original_draw(self, *args, **kwargs)
plotting.Legend.Draw = _monkey_patch_legend_draw

class LegendDefinition(object):
    def __init__(self, title='', labels=[], position=''):
        self.title = title
        self.labels = labels
        self.position = position
        
    @property
    def title(self):
        return self.title
    @title.setter
    def title(self, title):
        self.title=title
    @property
    def labels(self):
        return self.labels
    @labels.setter
    def labels(self, labels):
        self.labels=labels
    @property
    def position(self):
        return self.position
    @position.setter
    def position(self, position):
        self.position=position
    
    

class BasePlotter(object):
    def __init__(self, files, lumifiles, outputdir, 
                 styles=data_styles, blinder=None, forceLumi=-1, 
                 fileMapping=True):
        ''' Initialize the Plotter object

        Files should be a list of SAMPLE_NAME.root files.
        Lumifiles should contain floats giving the effective luminosity of
        each of the files.

        If [blinder] is not None, it will be applied to the data view.
        '''
        self.set_style()
        self.outputdir = outputdir
        self.base_out_dir = outputdir
        self.views = data_views(files, lumifiles, styles, forceLumi)
        self.canvas = plotting.Canvas(name='adsf', title='asdf')
        self.canvas.cd()
        self.pad    = plotting.Pad('up', 'up', 0., 0., 1., 1.) #ful-size pad
        self.pad.Draw()
        self.pad.cd()
        self.lower_pad = None
        if blinder:
            # Keep the unblinded data around if desired.
            self.views['data']['unblinded_view'] = self.views['data']['view']
            # Apply a blinding function
            self.views['data']['view'] = blinder(self.views['data']['view'])
        self.data = self.views['data']['view'] if 'data' in self.views else None
        self.keep = []
        # List of MC sample names to use.  Can be overridden.
        self.mc_samples = [i for i in self.views if not i.startswith('data')]

        file_to_map = filter(lambda x: x.startswith('data_'), self.views.keys())
        if not file_to_map: #no data here!
            file_to_map = self.views.keys()[0]
        else:
            file_to_map = file_to_map[0]
        #set_trace()
        self.file_dir_structure = Plotter.map_dir_structure( self.views[file_to_map]['file'] )


    def set_style(self):
        # For the canvas:
        ROOT.gStyle.SetCanvasBorderMode(0)
        ROOT.gStyle.SetCanvasColor(kWhite)
        ROOT.gStyle.SetCanvasDefH(600) # Height of canvas
        ROOT.gStyle.SetCanvasDefW(600) # Width of canvas
        ROOT.gStyle.SetCanvasDefX(0) # Position on screen
        ROOT.gStyle.SetCanvasDefY(0)
        
        # For the Pad:
        ROOT.gStyle.SetPadBorderMode(0)
        ROOT.gStyle.SetPadColor(kWhite)
        ROOT.gStyle.SetPadGridX(false)
        ROOT.gStyle.SetPadGridY(false)
        ROOT.gStyle.SetGridColor(0)
        ROOT.gStyle.SetGridStyle(3)
        ROOT.gStyle.SetGridWidth(1)
        
        # For the frame:
        ROOT.gStyle.SetFrameBorderMode(0)
        ROOT.gStyle.SetFrameBorderSize(1)
        ROOT.gStyle.SetFrameFillColor(0)
        ROOT.gStyle.SetFrameFillStyle(0)
        ROOT.gStyleSetFrameLineColor(1)
        ROOT.gStyle.SetFrameLineStyle(1)
        ROOT.gStyle.SetFrameLineWidth(1)
        
        # For the histo:
        # ROOT.gStyle.SetHistFillColor(1)
        # ROOT.gStyle.SetHistFillStyle(0)
        ROOT.gStyle.SetHistLineColor(1)
        ROOT.gStyle.SetHistLineStyle(0)
        ROOT.gStyle.SetHistLineWidth(1)
        # ROOT.gStyle.SetLegoInnerR(Float_t rad = 0.5)
        # ROOT.gStyle.SetNumberContours(Int_t number = 20)
        
        ROOT.gStyle.SetEndErrorSize(2)
        #  ROOT.gStyle.SetErrorMarker(20)
        ROOT.gStyle.SetErrorX(0.)
        
        ROOT.gStyle.SetMarkerStyle(20)
        
        # For the fit/function:
        ROOT.gStyle.SetOptFit(1)
        ROOT.gStyle.SetFitFormat("5.4g")
        ROOT.gStyle.SetFuncColor(2)
        ROOT.gStyle.SetFuncStyle(1)
        ROOT.gStyle.SetFuncWidth(1)
        
        # For the date:
        ROOT.gStyle.SetOptDate(0);
        # ROOT.gStyle.SetDateX(Float_t x = 0.01)
        # ROOT.gStyle.SetDateY(Float_t y = 0.01)
        
        # For the statistics box:
        ROOT.gStyle.SetOptFile(0)
        ROOT.gStyle.SetOptStat(1110) # To display the mean and RMS:   SetOptStat("mr")
        ROOT.gStyle.SetStatColor(kWhite)
        ROOT.gStyle.SetStatFont(42)
        ROOT.gStyle.SetStatFontSize(0.025)
        ROOT.gStyle.SetStatTextColor(1)
        ROOT.gStyle.SetStatFormat("6.4g")
        ROOT.gStyle.SetStatBorderSize(1)
        ROOT.gStyle.SetStatH(0.1)
        ROOT.gStyle.SetStatW(0.15)
        # ROOT.gStyle.SetStatStyle(Style_t style = 1001)
        # ROOT.gStyle.SetStatX(Float_t x = 0)
        # ROOT.gStyle.SetStatY(Float_t y = 0)
        
        # Margins:
        ROOT.gStyle.SetPadTopMargin(0.1)
        ROOT.gStyle.SetPadBottomMargin(0.14)
        ROOT.gStyle.SetPadLeftMargin(0.18)
        ROOT.gStyle.SetPadRightMargin(0.035)
        
        # For the Global title:
        ROOT.gStyle.SetOptTitle(1)
        ROOT.gStyle.SetTitleFont(42)
        ROOT.gStyle.SetTitleColor(1)
        ROOT.gStyle.SetTitleTextColor(1)
        ROOT.gStyle.SetTitleFillColor(0)
        ROOT.gStyle.SetTitleFontSize(0.04)
        # ROOT.gStyle.SetTitleH(0) # Set the height of the title box
        # ROOT.gStyle.SetTitleW(0) # Set the width of the title box
        ROOT.gStyle.SetTitleX(0.55) # Set the position of the title box
        ROOT.gStyle.SetTitleY(0.95) # Set the position of the title box
        # ROOT.gStyle.SetTitleStyle(Style_t style = 1001)
        ROOT.gStyle.SetTitleAlign(22)
        ROOT.gStyle.SetTitleBorderSize(0)
        
        # For the axis titles:
        ROOT.gStyle.SetTitleColor(1, "XYZ")
        ROOT.gStyle.SetTitleFont(42, "XYZ")
        ROOT.gStyle.SetTitleSize(0.05, "XYZ")
        # ROOT.gStyle.SetTitleXSize(Float_t size = 0.02) # Another way to set the size?
        # ROOT.gStyle.SetTitleYSize(Float_t size = 0.02)
        ROOT.gStyle.SetTitleXOffset(1.1)
        ROOT.gStyle.SetTitleYOffset(1.5)
        # ROOT.gStyle.SetTitleOffset(1.1, "Y") # Another way to set the Offset
        
        # For the axis labels:
        ROOT.gStyle.SetLabelColor(1, "XYZ")
        ROOT.gStyle.SetLabelFont(42, "XYZ")
        ROOT.gStyle.SetLabelOffset(0.007, "XYZ")
        ROOT.gStyle.SetLabelSize(0.04, "XYZ")
        
        # For the axis:
        ROOT.gStyle.SetAxisColor(1, "XYZ")
        ROOT.gStyle.SetStripDecimals(kTRUE)
        ROOT.gStyle.SetTickLength(0.03, "XYZ")
        ROOT.gStyle.SetNdivisions(505, "X")
        ROOT.gStyle.SetNdivisions(510, "YZ")
        ROOT.gStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
        ROOT.gStyle.SetPadTickY(1)
        
        # Default to no-log plots:
        ROOT.gStyle.SetOptLogx(0)
        ROOT.gStyle.SetOptLogy(0)
        ROOT.gStyle.SetOptLogz(0)
        
        # Postscript options:
        ROOT.gStyle.SetPaperSize(20.,20.)
        # ROOT.gStyle.SetLineScalePS(Float_t scale = 3)
        # ROOT.gStyle.SetLineStyleString(Int_t i, const char* text)
        # ROOT.gStyle.SetHeaderPS(const char* header)
        # ROOT.gStyle.SetTitlePS(const char* pstitle)
        
        # ROOT.gStyle.SetBarOffset(Float_t baroff = 0.5)
        # ROOT.gStyle.SetBarWidth(Float_t barwidth = 0.5)
        # ROOT.gStyle.SetPaintTextFormat(const char* format = "g")
        # ROOT.gStyle.SetPalette(Int_t ncolors = 0, Int_t* colors = 0)
        # ROOT.gStyle.SetTimeOffset(Double_t toffset)
        # ROOT.gStyle.SetHistMinimumZero(kTRUE)
        
        ROOT.gStyle.SetPalette(1)
        
        ROOT.gStyle.cd()
         
       
    @staticmethod
    def divide(passed, total, graph, method="bayes"):
        xTitle = graph.GetXaxis().GetTitle()
        yTitle = graph.GetYaxis().GetTitle()
        if method == "bayes":
            graph.BayesDivide(passed,total)
        elif method == "clopperpeason":
            graph.Divide(passed, total,"cp")
        graph.GetXaxis().SetTitle(xTitle)
        graph.GetYaxis().SetTitle(yTitle)
        
    @staticmethod
    def find_difference_binning(first, second):
        diffXLowEdge = 0
        diffXUpEdge = 0
        diffYLowEdge = 0
        diffYUpEdge = 0
        if first.GetXaxis().GetXmin() != second.GetXaxis().GetXmin():
            logging.warning(
                'Lower edge of x axis is not the same for the two histograms'
                'The higher between the two will be used!')
            diffXLowEdge = max(first.GetXaxis().GetXmin(),second.GetXaxis().GetXmin())
        else:
            diffXLowEdge = first.GetXaxis().GetXmin()
        if first.GetYaxis().GetXmin() != second.GetYaxis().GetXmin():
            logging.warning(
                'Lower edge of y axis is not the same for the two histograms'
                'The higher between the two will be used!')
            diffYLowEdge = max(first.GetYaxis().GetXmin(),second.GetYaxis().GetXmin())
        else:
            diffYLowEdge = first.GetYaxis().GetXmin()
        if first.GetXaxis().GetXmax() != second.GetXaxis().GetXmax():
            logging.warning(
                'Upper edge of x axis is not the same for the two histograms'
                'The lower between the two will be used!')
            diffXUpEdge = min(first.GetXaxis().GetXmax(),second.GetXaxis().GetXmax())
        else:
            diffXUpEdge = first.GetXaxis().GetXmax()
        if first.GetYaxis().GetXmax() != second.GetYaxis().GetXmax():
            logging.warning(
                'Upper edge of y axis is not the same for the two histograms'
                'The lower between the two will be used!')
            diffYUpEdge = min(first.GetYaxis().GetXmax(),second.GetYaxis().GetXmax())
        else:
            diffYUpEdge = first.GetYaxis().GetXmax()
        
        sxbins = set()
        sybins = set()
        for i in range(first.GetXaxis().GetNbins() + 1):
            sxbins.add(first.GetXaxis().GetBinLowEdge(i))
        for i in range(second.GetXaxis().GetNbins() + 1):
            sxbins.add(second.GetXaxis().GetBinLowEdge(i))
        sxbins.add(first.GetXaxis().GetXmax())
        sxbins.add(second.GetXaxis().GetXmax())
        for i in range(first.GetYaxis().GetNbins() + 1):
            sybins.add(first.GetYaxis().GetBinLowEdge(i))
        for i in range(second.GetYaxis().GetNbins() + 1):
            sybins.add(second.GetYaxis().GetBinLowEdge(i))
        sybins.add(first.GetYaxis().GetXmax())
        sybins.add(second.GetYaxis().GetXmax())
        
        allxbins = list(sxbins)
        allxbins.sort()
        xbins=[]
        for ibin in allxbins:
            if ibin >=diffXLowEdge and ibin <= diffXUpEdge:
                xbins.append(ibin)
        allybins = list(sybins)
        allybins.sort()
        ybins=[]
        for ibin in allybins:
            if ibin >=diffYLowEdge and ibin <= diffYUpEdge:
                ybins.append(ibin)
        return [xbins, ybins]
    
    @staticmethod
    def same_bins(first, second):
        if first.GetDimension() != second.GetDimension():
            return False
        if first.GetXaxis().GetXmin() != second.GetXaxis().GetXmin():
            return False
        if first.GetXaxis().GetXmax() != second.GetXaxis().GetXmax():
            return False
        if first.GetXaxis().GetNbins() != second.GetXaxis().GetNbins():
            return False
        for ibin in range(first.GetXaxis().GetNbins() + 1):
            if first.GetXaxis().GetBinLowEdge(iBin) != second.GetXaxis().GetBinLowEdge(iBin):
                return False
        if first.GetDimension > 1:
            if first.GetYaxis().GetXmin() != second.GetYaxis().GetXmin():
                return False
            if first.GetYaxis().GetXmax() != second.GetYaxis().GetXmax():
                return False
            if first.GetYaxis().GetNbins() != second.GetYaxis().GetNbins():
                return False
            for ibin in range(first.GetYaxis().GetNbins() + 1):
                if first.GetYaxis().GetBinLowEdge(iBin) != second.GetYaxis().GetBinLowEdge(iBin):
                    return False
        if first.GetDimension > 2:
            if first.GetZaxis().GetXmin() != second.GetZaxis().GetXmin():
                return False
            if first.GetZaxis().GetXmax() != second.GetZaxis().GetXmax():
                return False
            if first.GetZaxis().GetNbins() != second.GetZaxis().GetNbins():
                return False
            for ibin in range(first.GetZaxis().GetNbins() + 1):
                if first.GetZaxis().GetBinLowEdge(iBin) != second.GetZaxis().GetBinLowEdge(iBin):
                    return False
        return True
    
    @staticmethod
    def symmetrize_histogram_in_x(histo, aroundlowedge):
        if aroundlowedge == True:
            centerofsymmetry = histo.GetXaxis().GetXmin()
        else:
            centerofsymmetry = histo.GetXaxis().GetXmax()
        ybins = []
        for i in range(histo.GetYaxis().GetNbins() + 1):
            ybins.append(histo.GetYaxis().GetBinLowEdge(i))
        ybins.append(histo.GetYaxis().GetXmax())
        
        xbinsin = []
        for i in range(histo.GetXaxis().GetNbins() + 1):
            xbinsin.append(histo.GetXaxis().GetBinLowEdge(i))
        xbinsin.append(histo.GetXaxis().GetXmax())
        
        xbins = []
        if centerofsymmetry == xbinsin[0]:
            for i in range(len(xbinsin), 0, -1):
                xbins.append(2*centerofsymmetry - xbinsin[i])
            for i in range(1, len(xbinsin)):
                xbins.append(xbinsin[i])
        elif centerofsymmetry == xbinsin[len(xbinsin)-1]:
            for i in range(0,len(xbinsin)):
                xbins.append(xbinsin[i])
            for i in range(len(xbinsin)-1, -1, -1):
                xbins.append(2*centerofsymmetry - xbinsin[i])
        
        name = histo.GetName()
        title = histo.GetTitle()
        xaxistitle = histo.GetXaxis().GetTitle()
        yaxistitle = histo.GetYaxis().GetTitle()
        
        histonew = plotting.Hist2D(len(xbins)-1, xbins, len(ybins)-1, ybins)
        histonew.SetName(name)
        histonew.SetTitle(title)
        histonew.GetXaxis().SetTitle(xaxistitle)
        histonew.GetYaxis().SetTitle(yaxistitle)
        
        for ix in range(0, len(xbinsin)):
            for iy in range(0, len(ybins)):
                if aroundlowedge == True:
                    xbin1 = ix + len(xbinsin)
                    xbin2 = len(xbinsin) - ix - 1
                else:
                    xbin1 = ix
                    xbin2 = 2 * len(xbinsin) - ix - 1
                content = histo.GetBinContent(ix+1, iy+1)
                histonew.SetBinContent(xbin1, iy+1, content)
                histonew.SetBinContent(xbin2, iy+1, content)
        return histonew
    
    @staticmethod
    def set_canvas_style(self, logscalex=False, logscaley=False, logscalez=False):
        self.canvas.UseCurrentStyle()
        if logscalex == True:
            self.canvas.SetLogx(1)
        else:
            self.canvas.SetLogx(0)
        if logscaley == True:
            self.canvas.SetLogy(1)
        else:
            self.canvas.SetLogy(0)
        if logscalez == True:
            self.canvas.SetLogz(1)
        else:
            self.canvas.SetLogz(0)
            
    @staticmethod
    def set_profile_style(p):
        p.UseCurrentStyle()
        p.SetMarkerStyle(3)
        
    @staticmethod
    def set_histo_style(histo, linestyle, markerstyle, linecolor):
        histo.UseCurrentStyle()
        histo.SetLineWidth(2)
        histo.SetLineStyle(linestyle)
        histo.SetMarkerStyle(markerstyle)
        histo.SetMarkerColor(linecolor)
        histo.SetLineColor(linecolor)
        histo.SetTitleFont(ROOT.gStyle.GetTitleFont())
        histo.SetTitleSize(ROOT.gStyle.GetTitleFontSize(), "")
        histo.SetStats(kFALSE)
        
    @staticmethod
    def set_stack_histo_style(histo, color):
        histo.UseCurrentStyle()
        histo.SetLineWidth(1)
        histo.SetMarkerColor(1)
        histo.SetLineColor(1)
        histo.SetFillColor(color)
        histo.SetTitleFont(ROOT.gStyle.GetTitleFont())
        histo.SetTitleSize(ROOT.gStyle.GetTitleFontSize(), "")
        histo.SetStats(kFALSE)
    
    @staticmethod
    def set_graph_style(graph, markerstyle, linecolor):
        graph.UseCurrentStyle()
        graph.SetMarkerStyle(markerstyle)
        graph.SetMarkerColor(linecolor)
        graph.SetLineColor(linecolor)
        
    @staticmethod
    def create_and_write_canvases(linestyle, markerstyle, color, logscalex, logscaley, histos):
        if len(histos) == 0:
            logging.warning('CreateAndWriteCanvases(...) : list of histograms to be plotted is empty!'
                'No canvases will be created!')
            return
        for histo in histos:
            canvasname = 'c' + histo.GetName()
            create_and_write_canvas(canvasname, linestyle, markerstyle, color, logscalex, logscaley, histo)
            
    @staticmethod
    def create_and_write_canvas(cname, linestyle, markerstyle, color, logscalex, logscaley, histo, write=True):
        c = plotting.Canvas(name=cname)
        set_canvas_style(c, logscalex, logscaley)
        set_histo_style(histo, linestyle, markerstyle, color)
        if linestyle != 0 or markerstyle == 0:
            plotoptions = "hist"
        else:
            plotoptions = "e1"
        c.cd()
        histo.Draw(plotoptions)
        c.RedrawAxis()
        c.Update()
        if write == True:
            c.Write()
        return c
    
    @staticmethod
    def create_and_write_canvas(cname, linestyles, markerstyles, colors, legend_definition, logscalex, logscaley, histos, write=True):
        if len(histos) == 0:
            logging.warning('create_and_write_canvas(): histograms list is empty! Returning...')
            return
        c = plotting.Canvas(name=cname)
        set_canvas_style(c, logscalex, logscaley)
        plotoptions = []
        for i in range (0, len(histos)+1):
            set_histo_style(histos[i], linestyles[i], markerstyles[i], colors[i])
            if linestyles[i] != 0 or markerstyles[i] == 0:
                plotoptions.append('hist')
            else:
                plotoptions.append('e1')
        c.cd()
        histos[0].Draw(plotoptions[0])
        for i in range (1, len(histos)+1):
            if 'e1' in plotoptions[i] or 'hist' in plotoptions[i]:
                histos[i].Draw(plotoptions[i]+' same')
            else:
                histos[i].Draw('same')
        plot_legend(c, histos, plotoptions, legend_definition)
        c.RedrawAxis()
        c.Update()
        if write == True:
            c.Write()
        return c
    
    @staticmethod
    def create_and_write_canvas_with_comparison(cname, linestyles, markerstyles, colors, legend_definition, logscalex, logscaley, histos, write = True, comparison = 'pull', stack = False):
        if len(histos) < 2:
            logging.warning('create_and_write_canvas_with_comparison(): Less than two histograms to compare! Returning.')
            return
        for histo in histos:
            set_trace()
            if issubclass(histo, plotting.TH2) or issubclass(histo, plotting.TH3):
                logging.warning('create_and_write_canvas_with_comparison(): Comparison plots are supported only for 1D histograms! Returning.')
                return 0
        c = plotting.Canvas(name=cname, title=histos[0].GetTitle())
        set_canvas_style(c, logscalex, logscaley)
        
        c.cd()
        pad1 = ROOT.TPad("pad1","",0,0.33,1,1,0,0,0)
        pad2 = ROOT.TPad("pad2","",0,0,1,0.33,0,0,0)
        set_canvas_style(pad1, logscalex, logscaley)
        pad1.SetBottomMargin(0.001)
        pad2.SetTopMargin(0.005)
        pad2.SetGridy(kTRUE)
        pad2.SetBottomMargin(pad2.GetBottomMargin()*3)
        pad1.Draw()
        pad2.Draw()
        
        pad1.cd()        
        plotoptions = []
        if stack == True:
            set_histo_style(histos[0], 0, markerstyles[0], colors[0])
            plotoptions.append('e x0')
            canvasname = cname
            stackname = 'hs' + canvasname[1:]
            histostack = ROOT.THStack(stackname, '')
            histosum = histos[1].Clone('histosum')
            histosum.SetMarkerStyle(0)
            histosum.SetFillStyle(0)
            for i in range(1,len(histos)):
                set_stack_histo_style(histos[i], colors[i])
                histostack.Add(histos[i])
                plotoptions.append('fill')
                if i > 1:
                    histosum.Add(histosum, histos[i])
                
        else:
            for i in range(0,len(histos)):
                set_histo_style(histos[i], linestyles[i], markerstyles[i], colors[i])
                if linestyles[i] != 0 or markerstyles[i] == 0:
                    plotoptions.append('hist')
                else:
                    plotoptions.append('e1')
        
        labelSizeFactor1 = (pad1.GetHNDC()+pad2.GetHNDC()) / pad1.GetHNDC()
        labelSizeFactor2 = (pad1.GetHNDC()+pad2.GetHNDC()) / pad2.GetHNDC()
        
        pad1.cd()
        histos[0].SetLabelSize(ROOT.gStyle.GetLabelSize()*labelSizeFactor1, "XYZ")
        histos[0].SetTitleSize(ROOT.gStyle.GetTitleSize()*labelSizeFactor1, "XYZ")
        histos[0].GetYaxis().SetTitleOffset(histos[0].GetYaxis().GetTitleOffset()/labelSizeFactor1)
        histos[0].Draw(plotOptions[0])
        yMin = histos[0].GetMinimum()
        yMax = histos[0].GetMaximum()
        yMinNew = yMin + (yMax-yMin)/100000000
        yMaxNew = yMax + (yMax-yMin)*0.2
        histos[0].GetYaxis().SetRangeUser(yMinNew,yMaxNew)
        if stack == True:
            pad1.cd()
            histostack.Draw("hist same")
            histosum.SetLineWidth(3)
            histosum.Draw("hist same")
            histos[0].Draw(plotOptions[0] + ' same')
            OOT.TH1.AddDirectory(False)
            histocomp = histos[0].Clone()
            ROOT.TH1.AddDirectory(True)
            histocomp.SetMarkerColor(1)
            histocomp.SetLineColor(1)
            for ibin in range(1,histos[0].GetNbinsX()+1):
                binContent1 = histos[0].GetBinContent(ibin)
                binContent2 = 0.
                binError1 = histos[0].GetBinError(ibin)
                binError2 = 0
                for ihisto in range(1,len(histos)):
                    binContent2 = binContent2 + histos[ihisto].GetBinContent(ibin)
                    ierror = histos[ihisto].GetBinError(ibin)
                    binError2 = binError2 + sqrt(binError2**2 + ierror**2) # FIXME: This is probably wrong! The first binError2 should not be there
                    #binError2 = + sqrt(binError2**2 + ierror**2)
                result = 0
                error = 0
                if comparison == 'pull':
                    error = sqrt(binError1**2 + binError2**2)
                    if error != 0:
                        result = (binContent1-binContent2)/error
                    else:
                        result = 9999
                    histocomp.SetBinContent(iBin, result)
                    histocomp.SetBinError(iBin,0.01)
                elif comparison == 'ratio':
                    if binContent1 != 0 and binContent2 != 0:
                        result = binContent1/binContent2
                        error = sqrt((binError1/binContent1)**2 + (binError2/binContent2)**2)*result
                    else:
                        result = 9999
                        error = 1
                    histocomp.SetBinContent(iBin, result)
                    histocomp.SetBinError(iBin,error)
                elif comparison == 'diff':
                    if binContent1 != 0:
                        result = (binContent1-binContent2)/binContent1
                        if binContent1-binContent2 != 0:
                            error = sqrt(((binError1**2+binError2**2)/(binContent1-binContent2))**2+(binError1/binContent1)**2)*result
                        else:
                            error = 9999
                    else:
                        result = 9999
                        error = 1
                    histocomp.SetBinContent(ibin, result)
                    histocomp.SetBinError(ibin,error)
        else:
            for i in range(1,len(histos)):
                pad1.cd()
                histos[i].SetLabelSize(ROOT.gStyle.GetLabelSize()*labelSizeFactor1, "XYZ")
                histos[i].SetTitleSize(ROOT.gStyle.GetTitleSize()*labelSizeFactor1, "XYZ")
                histos[i].Draw(plotoptions[i]+' same')
                pad2.cd()
                ROOT.TH1.AddDirectory(False)
                histocomp = histos[i].Clone()
                ROOT.TH1.AddDirectory(True)
                for ibin in range(1,histos[0].GetNbinsX()+1):
                    binContent1 = histos[0].GetBinContent(iBin)
                    binContent2 = histos[i].GetBinContent(iBin)
                    binError1 = histos[0].GetBinError(iBin)
                    binError2 = histos[i].GetBinError(iBin)
                    error = 0
                    result = 0
                    if comparison == 'pull':
                        error = sqrt(binError1*binError1 + binError2*binError2)
                        if error != 0:
                            result = (binContent1-binContent2)/error
                        else:
                            result = 9999
                        histocomp.SetBinContent(iBin, result)
                        histocomp.SetBinError(iBin,0.01)
                    elif comparison == 'ratio':
                        if binContent1 != 0 and binContent2 != 0:
                            result = binContent2/binContent1
                            error = sqrt((binError1/binContent1)**2 + (binError2/binContent2)**2)*result
                        else:
                            result = 9999
                            error = 1
                        histocomp.SetBinContent(iBin, result)
                        histocomp.SetBinError(iBin,error)
                    elif comparison == 'diff':
                        if binContent1 != 0:
                            result = (binContent1-binContent2)/binContent1
                            if binContent1-binContent2 != 0:
                                error = sqrt(((binError1**2+binError2**2)/(binContent1-binContent2))**2+(binError1/binContent1)**2)*result
                            else:
                                error = 9999
                        else:
                            result = 9999
                            error = 1
                        histocomp.SetBinContent(iBin, result)
                        histocomp.SetBinError(iBin,error)
                
                histocomp.SetLabelSize(ROOT.gStyle.GetLabelSize()*labelSizeFactor2, "XYZ")
                histocomp.SetTitleSize(ROOT.gStyle.GetTitleSize()*labelSizeFactor2, "XYZ")
                histocomp.GetYaxis().SetTitleOffset(histocomp.GetYaxis().GetTitleOffset()/labelSizeFactor2)
                if len(histos) == 2 or stack == True:
                    if comparison == 'pull':
                        histocomp.GetYaxis().SetTitle('Pull')
                    elif comparison == 'ratio':
                        histocomp.GetYaxis().SetTitle('Ratio')
                    elif comparison == 'diff':
                        histocomp.GetYaxis().SetTitle('Difference')
                else:
                    if comparison == 'pull':
                        histocomp.GetYaxis().SetTitle('Pulls')
                    elif comparison == 'ratio':
                        histocomp.GetYaxis().SetTitle('Ratios')
                    elif comparison == 'diff':
                        histocomp.GetYaxis().SetTitle('Differences')
                histocomp.SetTitle('')
                histocomp.SetStats(False)
                if i == 1:
                    histocomp.Draw("e1")
                    if comparison == 'pull':
                        histocomp.GetYaxis().SetRangeUser(-2.999,2.999)
                    elif comparison == 'ratio':
                        histocomp.GetYaxis().SetRangeUser(0.,1.999)
                    elif comparison == 'diff':
                        histocomp.GetYaxis().SetRangeUser(-0.499,0.499)
                    histocomp.GetYaxis().SetNdivisions(505)
                else:
                    histocomp.Draw("e1 same")
        
        pad1.cd()
        if stack == True:
            plot_legend(pad1, histos[0], histostack, plotoptions, legend_definition)            
        else:
            plot_legend(pad1, histos, plotoptions, legend_definition)
        pad1.Update()
        pad2.Update()
        c.Update()
        if write == True:
            c.Write()
        return c
    
    @staticmethod
    def create_and_write_canvas_with_2d_comparison(cname, ctitle, plotoptions, logscalex, logscaley, logscalez, histo1, histo2, write = True, comparison = 'pull'):
        if not same_bins(histo1, histo2):
            logging.error("create_and_write_canvas_with_2d_comparison(): the two histograms do not have the same binning! Exiting...")
            abort() # FIXME: to be changed!
        c = plotting.Canvas(cname)
        set_canvas_style(c, logscalex, logscaley, logscalez)
        c.SetRightMargin(c.GetRightMargin()*4.5)
        
        histocomp = plotting.Hist2D("histocomp", ctitle, histo1.GetXaxis().GetNbins(), histo1.GetXaxis().GetXmin(), histo1.GetXaxis().GetXmax(), histo1.GetYaxis().GetNbins(), histo1.GetYaxis().GetXmin(), histo1.GetYaxis().GetXmax(), histo1.GetXaxis().GetTitle(),  histo1.GetYaxis().GetTitle())
        if comparison == 'pull':
            for xbin in range(1, histo1.GetXaxis().GetNbins()+1):
                for ybin in range(1, histo1.GetYaxis().GetNbins()+1):
                    error = sqrt(histo1.GetBinError(xbin, ybin)**2 + histo2.GetBinError(xbin, ybin)**2)
                    if error != 0:
                        bincontent = (histo1.GetBinContent(xbin, ybin) - histo2.GetBinContent(xbin, ybin)) / error
                    else:
                        bincontent = 1e+9
                    histocomp.SetBinContent(xbin, ybin, bincontent)
        elif comparison == 'ratio':
            for xbin in range(1, histo1.GetXaxis().GetNbins()+1):
                for ybin in range(1, histo1.GetYaxis().GetNbins()+1):
                    if histo2.GetBinContent(xbin, ybin) != 0:
                        bincontent = histo1.GetBinContent(xbin, ybin) / histo2.GetBinContent(xbin, ybin)
                    else:
                        bincontent = 1e+9
                    histocomp.SetBinContent(xbin, ybin, bincontent)
        elif comparison == 'diff':
            histocomp.Add(histo1, histo2, 1, -1)
        elif comparison == "reldiff":
            for xbin in range(1, histo1.GetXaxis().GetNbins()+1):
                for ybin in range(1, histo1.GetYaxis().GetNbins()+1):
                    if histo1.GetBinContent(xbin, ybin) != 0:
                        bincontent = (histo1.GetBinContent(xbin, ybin) - histo2.GetBinContent(xbin, ybin)) / histo1.GetBinContent(xbin, ybin)
                    else:
                        bincontent = 1e+9
                    hstocomp.SetBinContent(xbin, ybin, bincontent)
            
        c.cd()
        histocomp.SetStats(False)
        histocomp.Draw(plotoptions)
        
        c.Update()
        if write == True:
            c.Write()
        return c
    
    @staticmethod
    def create_and_write_canvas(cname, markerstyles, colors, logscalex, logscaley, graphs, write = True):
        if len(graphs) == 0:
            logging.error('create_and_write_canvas(): list of graphs is empty! Returning...')
            return 0
        
        c = plotting.Canvas(cname)
        set_canvas_style(c, logscalex, logscaley)
        c.SetRightMargin(c.GetRightMargin()*3.5)
        
        plotoptions = []
        
        for i in range(0, len(graphs)+1):
            set_graph_style(graphs[i], markerstyles[i], colors[i])
            if i == 0:
                plotoptions.append('A P')
            else:
                plotoptions.append('P')
        
        c.cd()
        isFirst = True
        if graphs[0].GetN() != 0:
            graphs[0].Draw(plotoptions[0])
            isFirst = False
        else:
            logging.warning('create_and_write_canvas(): graph #0 has zero points, it will not be drawn')
        
        for i in range(1, len(graphs)):
            if graphs[i].GetN() != 0:
                if isFirst == True:
                    graphs[i].Draw('A ' + plotoptions[i])
                    isFirst = False
                else:
                    graphs[i].Draw(plotoptions[i] + ' same')
            else:
                logging.warning('create_and_write_canvas(): graph #%s has zero points, it will not be drawn' % i)
        
        c.Update()
        if write == True:
            c.Write()
        return c
    
    @staticmethod
    def create_and_write_canvas(cname, ctitle, plotoptions, legend_definition, logscalex, logscaley, logscalez, histo, write = True):
        c = plotting.Canvas(cname)
        set_canvas_style(c, logscalex, logscaley, logscalez)
        c.SetRightMargin(c.GetRightMargin()*4.5)
        
        c.cd()
        histo.SetTitle(ctitle)
        histo.SetStats(False)
        histo.Draw(plotoptions)
        PlotLegend(c, histo, plotoptions, legend_definition)
        
        c.Update()
        if write == True:
            c.Write()
        return c
    
    @staticmethod
    def create_and_write_canvas_3d(cname, ctitle, legend_definition, logscalex, logscaley, logscalez, phi, theta, histo, write = True):
        c = plotting.Canvas(cname)
        # To prevent root bug when histogram is flat
        if histo.GetMinimum() != histo.GetMaximum():
            set_canvas_style(c, logscalex, logscaley, logscalez)
        else:
            set_canvas_style(c, False, False, False)
        c.SetRangeUser(c.GetRightMargin()*6)
        
        c.cd()
        histo.SetTitle(title)
        histo.SetStats(False)
        histo.Draw('lego2 z')
        c.SetPhi(phi)
        c.SetTheta(theta)
        
        plot_legend(c, histo, 'lego2 z', legend_definition)
        c.update()
        if write == True:
            c.Write()
        return c
            
    @staticmethod
    def plot_legend(c, objects, plotoptions, legend_definition):
        # Create the legend
        # Set the legend position according to LegendDefinition::position variable
        legPosition = legend_definition.position
        padLeftMargin = c.GetLeftMargin()
        padRightMargin = c.GetRightMargin()
        padTopMargin = c.GetTopMargin()
        padBottomMargin = c.GetBottomMargin()
        plotWidth = 1. - (padLeftMargin + padRightMargin)
        plotHeight = 1. - (padTopMargin + padBottomMargin)
        nEntries = objects.size()
        maxTextSize = 0
        if legend_definition.title.size() > maxTextSize:
            maxTextSize = leg.title.size()
        if maxTextSize > 40:
            maxTextSize = 40
        for ientry in range(0, legend_definition.labels.size()):
            if legend_definition.labels[ientry].size() > maxTextSize:
                maxTextSize = legend_definition.labels[ientry].size()
        if legend_definition.title.length() > 0:
            nentries = nentries + 1
        if  'e' in legPosition or 'E' in legPosition:
            legX1 = (0.95-maxTextSize*0.012-0.1)*plotWidth + padLeftMargin
            legX2 = 0.95*plotWidth + padLeftMargin
        elif 'w' in legPosition or 'W' in legPosition:
            legX1 = 0.05*plotWidth + padLeftMargin
            legX2 = (0.05+maxTextSize*0.012+0.1)*plotWidth + padLeftMargin
        else:
            legX1 = 0.325*plotWidth + padLeftMargin
            legX2 = 0.675*plotWidth + padLeftMargin
        if 'n' in legPosition or 'N' in legPosition:
            y1 = 0.95 - (0.1*nentries)
            if y1 < 0.5:
                y1 = 0.5
            legY1 = y1*plotHeight + padBottomMargin
            legY2 = 0.95*plotHeight + padBottomMargin
        elif 's' in legPosition or 'S' in legPosition:
            y2 = 0.05 + (0.1*nentries)
            if y2 > 0.5:
                y2 = 0.5
            legY1 = 0.05*plotHeight + padBottomMargin
            legY2 = y2*plotHeight + padBottomMargin
        else:
            y1 = 0.5 - (0.05*nentries)
            if y1 < 0.25:
                y1 = 0.25
            y2 = 0.5 + (0.05*nentries)
            if y2 > 0.75:
                y2 = 0.75
            legY1 = y1*plotHeight + padBottomMargin
            legY2 = y2*plotHeight + padBottomMargin
        legendoptions = []
        for i in range(0, len(plotoptions)):
            if 'e' in plotoptions[i] or 'P' in plotoptions[i]:
                legendoptions.append('lp')
            elif 'fill' in plotoptions[i]:
                legendoptions.append('f')
            else:
                legendoptions.append('l')
        
        legend  = plotting.TLegend(legX1,legY1, legX2, legY2, legend_definition.title, 'NDC')
        
        # Set generic options
        legend.UseCurrentStyle()
        legend.SetBorderSize(0)
        legend.SetFillColor(0)
        legend.SetFillStyle(0)
        legend.SetTextFont(42)
        legend.SetTextSize(0.045)
          
        for i in range(0, len(objects)):
            legend.AddEntry(objects[i], legend_definition.labels[i], legendoptions[i])
        
        c.cd()
        legend.Draw()
    
    @staticmethod
    def parse_formula(fcn_string, pars_string):
        '''Parses a formula similar to a roofit workspace,
        but uses root to make things little easier.
        Produces a TF1
        
        Example: 
        parse_formula(
            "slope*x + constant", 
            "slope[0,-1,1], constant[-1]"
        )
        produces a linear function with slope in [-1,1] 
        initialized at 0 and a constant fixed at -1'''
        pars       = []
        formula    = fcn_string
        for par_num, match in enumerate(re.finditer("(?P<name>\w+)(?P<boundaries>\[[^\]]+\]),? ?", pars_string)):
            par        = Struct()
            par.num    = par_num
            par.name   = match.group('name')
            par.bounds = eval( match.group('boundaries') )
            formula    = formula.replace(par.name, '[%i]' % par.num)
            pars.append(par)

        ret = ROOT.TF1('ret', formula, 0, 200)
        for par in pars:
            ret.SetParName(par.num, par.name)
            if len(par.bounds) == 1:
                ret.FixParameter(par.num, par.bounds[0])
            else:
                ret.SetParameter(par.num, par.bounds[0])
                ret.SetParLimits(par.num, par.bounds[1], par.bounds[2])
        return ret






    def add_legend(self, samples, leftside=True, entries=None):
        ''' Build a legend using samples.

        If entries is None it will be taken from len(samples)

        '''
        nentries = entries if entries is not None else len(samples)
        legend = None
        if leftside:
            legend = plotting.Legend(nentries, leftmargin=0.03, topmargin=0.05, rightmargin=0.65)
        else:
            legend = plotting.Legend(nentries, rightmargin=0.07, topmargin=0.05, leftmargin=0.45)
        for sample in samples:
            if isinstance(sample, plotting.HistStack):
                for s in sample:
                    if getattr(sample, 'inlegend', True):
                        label = s.GetTitle()
                        style = s.legendstyle
                        legend.AddEntry(s, style, label) 
            else:
                legend.AddEntry(sample)
        legend.SetEntrySeparation(0.0)
        legend.SetMargin(0.35)
        legend.Draw()
        self.keep.append(legend)
        return legend

    def add_cms_blurb(self, sqrts, preliminary=True, lumiformat='%0.1f'):
        ''' Add the CMS blurb '''
        latex = ROOT.TLatex()
        latex.SetNDC();
        latex.SetTextSize(0.04);
        latex.SetTextAlign(31);
        latex.SetTextAlign(11);
        label_text = "CMS"
        if preliminary:
            label_text += " Preliminary"
        label_text += " %i TeV " % sqrts
        label_text += (lumiformat + " fb^{-1}") % (
            self.views['data']['intlumi']/1000.)
        self.keep.append(latex.DrawLatex(0.18,0.96, label_text));



    def make_text_box(self, text, position='top-right'):
        '''Adds a text box in the main pad'''
        look_up_positions = {
            'top-right'    : (0.73, 0.67, 0.96, 0.92),
            'top-left'     : (0.16, 0.67, 0.39, 0.92),
            'bottom-right' : (0.73, 0.15, 0.96, 0.4),
            'bottom-left'  : (0.16, 0.15, 0.39, 0.4),
            }
        p = look_up_positions[position] if isinstance(position, str) \
                         else position
        stat_box = ROOT.TPaveText(p[0], p[1], p[2], p[3], 'NDC')
        for line in text.split('\n'):
            print line
            stat_box.AddText(line)
        
        #Set some graphics options not to suck
        stat_box.SetFillColor(0)
        stat_box.SetBorderSize(1)
        return stat_box

    def reset(self):
        '''hard graphic reset'''
        del self.canvas
        del self.pad
        del self.lower_pad
        self.keep = []
        self.canvas = plotting.Canvas(name='adsf', title='asdf')
        self.canvas.cd()
        self.pad    = plotting.Pad('up', 'up', 0., 0., 1., 1.) #ful-size pad
        self.pad.Draw()
        self.pad.cd()
        self.lower_pad = None

    def save(self, filename, png=True, pdf=True, dotc=False, dotroot=False, json=False, verbose=False):
        ''' Save the current canvas contents to [filename] '''
        self.pad.Draw()
        self.canvas.Update()
        if not os.path.exists(self.outputdir):
            os.makedirs(self.outputdir)
        if verbose:
            print 'saving '+os.path.join(self.outputdir, filename) + '.png'
        if png: self.canvas.SaveAs(os.path.join(self.outputdir, filename) + '.png')
        if pdf: self.canvas.SaveAs(os.path.join(self.outputdir, filename) + '.pdf')
        if dotc:
            self.canvas.SaveAs(os.path.join(self.outputdir, filename) + '.C')
        if json:
            jdict = {}
            for obj in self.keep:
                if isinstance(obj, ROOT.TH1):
                    jdict[obj.GetTitle()] = [obj.GetBinContent(1), obj.GetBinError(1)] 
                if isinstance(obj, ROOT.THStack):
                    jdict['hist_stack'] = {}
                    for i in obj.GetHists():
                        jdict['hist_stack'][i.GetTitle()] = [i.GetBinContent(1), i.GetBinError(1)]
            with open(os.path.join(self.outputdir, filename) + '.json', 'w') as jout:
                jout.write(prettyjson.dumps(jdict))
        if dotroot:
            logging.error(
                'This functionality still has to be implemented '
                'properly, due to the awsome ROOT "features"')
            rfile = os.path.join(self.outputdir, filename) + '.root'
            with io.root_open(rfile, 'recreate') as tfile:
                #set_trace()
                self.canvas.Write()
                for obj in self.keep:
                    if isinstance(obj, plotting.HistStack):
                        for hist in obj.hists:
                            hist.Write()
                    obj.Write()
            #self.keep = []
            self.reset()

        if self.keep and self.lower_pad:
            #pass
            self.reset()
        else:
            # Reset keeps
            self.keep = []
        # Reset logx/y
        self.canvas.SetLogx(False)
        self.canvas.SetLogy(False)
        
    def plot(self, sample, path, drawopt='', rebin=None, styler=None, xaxis='', xrange=None):
        ''' Plot a single histogram from a single sample.

        Returns a reference to the histogram.
        '''
        view = self.views[sample]['view']
        if rebin:
            view = self.rebin_view(view, rebin)
        histo = view.Get(path)
        if xrange:
            histo.GetXaxis().SetRange(xrange[0], xrange[1])
        if styler:
            styler(histo)
        histo.Draw(drawopt)
        histo.GetXaxis().SetTitle(xaxis)
        self.keep.append(histo)
        return histo


