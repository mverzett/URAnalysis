#! /usr/bin/env python

from pdb import set_trace
from URAnalysis.Utilities.rootbindings import ROOT
import math
import numpy.random
import rootpy.io
from rootpy import asrootpy
import rootpy.plotting as plotting
from URAnalysis.Utilities.decorators import asrpy
import uuid

from rootpy import log
log = log["/URUnfolding"]
rootpy.log.basic_config_colorized()
ROOT.TH1.AddDirectory(False)

class URUnfolding(object):
    orientations = {'Horizontal':ROOT.TUnfold.kHistMapOutputHoriz, 
                    'Vertical':ROOT.TUnfold.kHistMapOutputVert}
    regularizations = {'None':ROOT.TUnfold.kRegModeNone, 
                       'Size':ROOT.TUnfold.kRegModeSize, 
                       'Derivative':ROOT.TUnfold.kRegModeDerivative, 
                       'Curvature':ROOT.TUnfold.kRegModeCurvature, 
                       'Mixed':ROOT.TUnfold.kRegModeMixed}
    constraints = {'None':ROOT.TUnfold.kEConstraintNone, 
                   'Area':ROOT.TUnfold.kEConstraintArea}
    densities = {'None':ROOT.TUnfoldDensity.kDensityModeNone, 
                 'BinWidth':ROOT.TUnfoldDensity.kDensityModeBinWidth, 
                 'User':ROOT.TUnfoldDensity.kDensityModeUser, 
                 'BinWidthAndUser':ROOT.TUnfoldDensity.kDensityModeBinWidthAndUser}
    scantaumodes = {'RhoAvg':ROOT.TUnfoldDensity.kEScanTauRhoAvg,
                    'RhoMax':ROOT.TUnfoldDensity.kEScanTauRhoMax,
                    'RhoAvgSys':ROOT.TUnfoldDensity.kEScanTauRhoAvgSys,
                    'RhoMaxSys':ROOT.TUnfoldDensity.kEScanTauRhoMaxSys,
                    'RhoSquareAvg':ROOT.TUnfoldDensity.kEScanTauRhoSquareAvg,
                    'RhoSquareAvgSys':ROOT.TUnfoldDensity.kEScanTauRhoSquareAvgSys}

    def __init__(self, 
                 truthfilename = '/uscms/home/mgalanti/nobackup/URAnalysis/CMSSW_7_2_3_patch1/src/URAnalysis/ttJets_pu30.root', 
                 measuredfilename='/uscms/home/mgalanti/nobackup/URAnalysis/CMSSW_7_2_3_patch1/src/URAnalysis/ttJets_pu30.root',  
                 distribution = 'topptlep', 
                 scale = 1., 
                 orientation = 'Horizontal', 
                 regmode = 'Curvature', 
                 constraint = 'Area', 
                 density = 'BinWidthAndUser'):
        self.unfoldingdone = False
        self.unfoldingparam = 0.1
        self.scale = scale
        
        self.distribution = distribution
        self.truthfilename = truthfilename
        self.measuredfilename = measuredfilename
        
        self.orientation = orientation
        self.regmode = regmode
        self.constraint = constraint
        self.density = density

        #TO BE DEFINED AFTERWARDS
        self.measured = None
        self.matrix = None
        self.truth = None         
        self.unfolder = None
        self.cov_matrix = None

    def InitUnfolder(self):        
        log.warning("Setting underflow and overflow bins to zero! This must be removed once the binning is corrected.")
        #for ix in range(0,self.matrix.GetNbinsX()+1):
        #    self.matrix.SetBinContent(ix,0,0)
        #    self.matrix.SetBinContent(ix,self.matrix.GetNbinsY()+1,0)
        #for iy in range(0,self.matrix.GetNbinsY()+1):
        #    self.matrix.SetBinContent(0,iy,0)  
        #    self.matrix.SetBinContent(self.matrix.GetNbinsX()+1,iy,0)
         
        self.ScaleDistributions(self.scale)

        log.debug('Initializing unfolder.')
        self.unfolder = ROOT.TUnfoldDensity(
            self.matrix,
            URUnfolding.orientations[self.orientation],
            URUnfolding.regularizations[self.regmode],
            URUnfolding.constraints[self.constraint],
            URUnfolding.densities[self.density])
        log.debug('Loading histogram %s into unfolder' %self.measured.GetName() )
        status = self.unfolder.SetInput(self.measured,0.,0.,self.cov_matrix)
        if status >= 10000:
            raise RuntimeError('Unfolding status %i. Unfolding impossible!'%status)
        
        
    def ScaleDistributions(self, scalefactor):
        self.matrix.scale(scalefactor)
        self.truth.scale(scalefactor)
        self.measured.scale(scalefactor)
        self.unfoldingdone = False

    def LoadMatrix(self, basename='truth_response_', suffix='_matrix',  distribution='topptlep', filename=None, filedir='TRUTH'):
        self.unfoldingdone = False
        if filename is None:
            filename = self.truthfilename
        log.debug('Loading matrix for distribution "%s" from file "%s"' %(distribution,filename))
        myfile = rootpy.io.root_open(filename, 'read')
        mydir = getattr(myfile,filedir)
        self.matrix = getattr(mydir,basename+distribution+suffix)
        myfile.close()

    def LoadTruth(self, basename='truth_response_', suffix='_truth', distribution='topptlep', filename=None, filedir='TRUTH'):
        self.unfoldingdone = False
        if filename is None:
            filename = self.truthfilename
        log.debug('Loading truth for distribution "%s" from file "%s"' %(distribution,filename))
        myfile = rootpy.io.root_open(filename, 'read')
        mydir = getattr(myfile,filedir)
        self.truth = getattr(mydir,basename+distribution+suffix)
        myfile.close()

    def LoadMeasured(self, basename='truth_response_', suffix='_measured', distribution='topptlep', filename=None, filedir='TRUTH'):
        self.unfoldingdone = False
        if filename is None:
            filename = self.measuredfilename
        log.debug('Loading measured for distribution "%s" from file "%s"' %(distribution,filename))
        myfile = rootpy.io.root_open(filename, 'read')
        mydir = getattr(myfile, filedir)
        self.measured = getattr(mydir, basename+distribution+suffix)
        myfile.close()

    def DoUnfolding(self, unfoldingparam = None):
        if unfoldingparam is None:
            unfoldingparam = self.unfoldingparam
        else:
            self.unfoldingdone = False
        if self.unfoldingdone == False:
            log.debug('Unfolding distribution "%s" using regularization parameter %f' % (self.measured.GetName(), unfoldingparam))
            self.unfolder.DoUnfold(unfoldingparam)
            self.unfoldingdone = True
        
    @asrpy
    def DoScanTau(self, npoints, tau_min=0., tau_max=20., mode='RhoAvg'):
        scan_mode = URUnfolding.scantaumodes['RhoAvg']
        spline = ROOT.TSpline3()
        best = self.unfolder.ScanTau(
            npoints, tau_min, tau_max, 
            spline, scan_mode
            )
        #, const char* distribution = 0, const char* projectionMode = 0, TGraph** lCurvePlot = 0, TSpline** logTauXPlot = 0, TSpline** logTauYPlot = 0)
        #convert spline in Graph
        step = (tau_max - tau_min)/float(npoints)
        x_vals = []
        y_vals = []
        val = tau_min
        while val < tau_max:
            x_vals.append(val)
            y_vals.append(
                spline.Eval(val)
                )
            val += step
        tcurve = plotting.Graph(100)
        for idx, xy in enumerate(zip(x_vals, y_vals)):
            tcurve.SetPoint(idx, *xy)
        return tau_min+step*best, tcurve

    @asrpy
    def DoScanLcurve(self, npoints, tau_min=0, tau_max=20):
        lcurve = ROOT.TGraph()
        best = self.unfolder.ScanLcurve(
            npoints,
            tau_min,
            tau_max,
            lcurve
            )
        step = float(tau_max-tau_min)/npoints
        return tau_min+best*step, lcurve

    @property
    def tau(self):
        return self.unfoldingparam
    
    @tau.setter
    def tau(self, val):
        if val != self.unfoldingparam:
            self.unfoldingparam = val
            self.unfoldingdone = False
        
    @asrpy
    def GetUnfolded(self, unfoldingparam = None, name="Unfolded"):
        self.DoUnfolding(unfoldingparam)
        return self.unfolder.GetOutput(name)

    @property
    def unfolded(self):
        self.DoUnfolding()
        return self.unfolder.GetOutput(uuid.uuid4().hex)

    @asrpy
    def GetRefolded(self):
        self.DoUnfolding()
        return self.unfolder.GetFoldedOutput("Refolded")

    @property
    def refolded(self):
        return self.GetRefolded()

    @asrpy
    def GetEmatrixTotal(self, name):
        self.DoUnfolding()
        return self.unfolder.GetEmatrixTotal(name)

    @property
    def ematrix_total(self):
        return self.unfolder.GetEmatrixTotal(
            uuid.uuid4().hex
            )
    
    @asrpy
    def GetRhoItotal(self, name):
        self.DoUnfolding()
        return self.unfolder.GetRhoItotal(name)

    @property
    def rhoI_total(self):
        return self.GetRhoItotal(uuid.uuid4().hex)

    @property
    @asrpy
    def bias(self):
        self.DoUnfolding()
        return self.unfolder.GetBias(uuid.uuid4().hex)

    def Generate(self, numevents):
        if (not hasattr(self,'gentruth')) or self.gentruth == 0:
            self.hmiss = ROOT.TH1D(self.truth)
            self.hmiss.Add(self.matrix.ProjectionX(), -1.)
            self.hfake = ROOT.TH1D(self.measured)
            self.hfake.Add(self.hmatrix.ProjectionY(), -1.)
            self.gentruth = ROOT.TH1D(self.htruth)
            self.genmeasured = ROOT.TH1D(self.htruth)
            maxima = [self.hmiss.GetMaximum(), self.hfake.GetMaximum(), self.matrix.GetMaximum()]
            maxima.sort()
            self.maxval = maxima[2]
            newfile = rootpy.io.root_open("output_prova2.root", 'recreate')
            self.hmiss.Write()
            self.hfake.Write()
            self.gentruth.Write()
            self.genmeasured.Write()
            newfile.Close()
        self.gentruth.Reset()
        self.genmeasured.Reset()
        nev = numpy.random.poisson(numevents)
        print "nev =", nev
        nbinsx = self.hmiss.GetNbinsX()
        nbinsy = self.hfake.GetNbinsX()
        print "nbinsx, nbinsy =", nbinsx,nbinsy
        while nev != 0:
            #if nev%1000 == 0:
            #   print "nev =",nev
            binx = numpy.random.random_integers(0,nbinsx)
            biny = numpy.random.random_integers(0,nbinsy)
            test = numpy.random.uniform(0,self.maxval)
            if binx > 0 and biny > 0:
                dest = self.matrix.GetBinContent(binx, biny)
                if test < dest:
                    nev = nev-1
                    self.gentruth.SetBinContent(binx, self.gentruth.GetBinContent(binx)+1)
                    self.genmeasured.SetBinContent(biny, self.genmeasured.GetBinContent(biny)+1)
            elif binx == 0:
                dest = self.hfake.GetBinContent(biny)
                if test < dest:
                    nev = nev-1
                    self.genmeasured.SetBinContent(biny, self.genmeasured.GetBinContent(biny)+1)
            elif biny == 0:
                dest = self.hmiss.GetBinContent(binx)
                if test < dest:
                    self.gentruth.SetBinContent(binx, self.gentruth.GetBinContent(binx)+1)
        for i in range(1,nbinsx+1):
            self.gentruth.SetBinError(i, math.sqrt(self.gentruth.GetBinContent(i)))
        for i in range(1,nbinsy+1):
            self.genmeasured.SetBinError(i, math.sqrt(self.genmeasured.GetBinContent(i)))

    def StatTest(self,numexp):
        diff = ROOT.TH1D(self.hmeasured)
        diffq = ROOT.TH1D(self.hmeasured)
        diff.Reset()
        diffq.Reset()
        numevents = self.hmeasured.Integral()
        for exp in range(0,numexp):
            self.Generate(numevents)
            genunfolded = self.GetUnfolded(self.genmeasured)
            print "exp",self.gentruth.Integral(),genunfolded.Integral(),self.genmeasured.Integral(),numevents
            for b in range(1,genunfolded.GetNbinsX()+1):
                bdiff = genunfolded.GetBinContent(b) - self.gentruth.GetBinContent(b)
                diff.SetBinContent(b,diff.GetBinContent(b)+bdiff)
                diffq.SetBinContent(b,diff.GetBinContent(b)+bdiff*bdiff)
        for b in range(1,diff.GetNbinsX()+1):
            mean = diff.GetBinContent(b)/float(numexp)
            meanq = diff.GetBinContent(b)/float(numexp)
            diff.SetBinContent(b, mean/self.gentruth.GetBinContent(b))
            diff.SetBinError(b, math.sqrt(abs(meanq-mean*mean))/self.gentruth.GetBinContent(b))
        return diff

    def write_to(self, tdir, name):
        unfold_dir = tdir.mkdir(name)
        unfold_dir.cd()
        written = 0
        def write_txt(txt, name):
            if txt:
                ttxt = ROOT.TText(0.,0.,txt)
                ttxt.SetName(name)
                return ttxt.Write()
            else:
                return 0.

        def write_hist(h, name):
            if h:
                h.SetName(name)
                return h.Write()
            else:
                return 0.

        def write_float(h, name):
            return ROOT.RooRealVar(name, name, h).Write()
        written += write_txt(self.unfoldingdone.__repr__(), 'bool_unfoldingdone')
        written += write_float(self.unfoldingparam, 'unfoldingparam')
        written += write_float(self.scale, 'scale')
        
        written += write_txt(self.distribution, 'distribution')
        written += write_txt(self.truthfilename, 'truthfilename')
        written += write_txt(self.measuredfilename, 'measuredfilename')
        
        written += write_txt(self.orientation, 'orientation')
        written += write_txt(self.regmode    , 'regmode')
        written += write_txt(self.constraint , 'constraint')
        written += write_txt(self.density    , 'density')

        #TO BE DEFINED AFTERWARDS
        written += write_hist(self.measured, 'measured')
        written += write_hist(self.matrix, 'matrix')
        written += write_hist(self.truth, 'truth')
        written += write_hist(self.cov_matrix, 'cov_matrix')
        #written += self.unfolder.Write() if self.unfolder else 0.
        return written

    @classmethod
    def read_from(unfolder, tdir):
        #still experimental
        keys = dict((i.GetName(), i.ReadObj()) for i in tdir.GetListOfKeys())
        unfolder.unfoldingdone = eval(keys['bool_unfoldingdone'])
        unfolder.unfoldingparam = keys['unfoldingparam'].getVal()
        unfolder.scale = keys['scale'].getVal()
        
        unfolder.distribution     = keys['distribution'    ].GetTitle()
        unfolder.truthfilename    = keys['truthfilename'   ].GetTitle()
        unfolder.measuredfilename = keys['measuredfilename'].GetTitle()
        
        unfolder.orientation= keys['orientation'].GetTitle()
        unfolder.regmode    = keys['regmode'    ].GetTitle()
        unfolder.constraint = keys['constraint' ].GetTitle()
        unfolder.density    = keys['density'    ].GetTitle()

        #TO BE DEFINED AFTERWARDS
        unfolder.measured = keys.get('measured', None)
        unfolder.matrix   = keys.get('matrix'  , None)
        unfolder.truth    = keys.get('truth'   , None)
        unfolder.cov_matrix = keys.get('cov_matrix', None)  
        #written += self.unfolder.Write() if self.unfolder else 0.
        if unfolder.unfoldingdone:
            unfolder.InitUnfolder()
            #trigger unfolding!
            unfolder.unfoldingdone = False
            unfolder.DoUnfolding()
        return unfolder

def testUnfolding(datafile = '', hist = ''):
    responsefile = '/uscms/home/mgalanti/nobackup/URAnalysis/CMSSW_7_2_3_patch1/src/URAnalysis/ttJets_pu30.root'
    #datafile = responsefile # Need to run on a datafile different from the responsefile!
    datafile = '/uscms/home/mgalanti/nobackup/URAnalysis/CMSSW_7_2_3_patch1/src/URAnalysis/AnalysisTools/python/unfolding/ptthad.harvested.root'
    hist = 'toppthad'
    scale = 5000.*806./13977743. # NO idea yet what this means
    scale = 1.
    myunfolding = URUnfolding(truthfilename=responsefile, measuredfilename=datafile, distribution=hist, scale=scale)
    myunfolding.LoadMatrix(distribution = myunfolding.distribution)
    myunfolding.LoadTruth(distribution = myunfolding.distribution)
    # myunfolding.LoadMeasured(distribution = myunfolding.distribution)
    myunfolding.LoadMeasured(distribution = 'tt_right', basename = '', suffix='', filedir = 'ptthad')
    myunfolding.InitUnfolder()
    # fdata = rootpy.io.root_open(datafile, 'read')
    # hdata = getattr(fdata,'fitsum') # This was the original line defining hdata
    hdata = asrootpy(myunfolding.measured) # Duplicate. Remove!
    hdata_unfolded = asrootpy(myunfolding.GetUnfolded(0.1))
    tau_curve = myunfolding.DoScanLcurve(100)
    hdata_refolded = asrootpy(myunfolding.GetRefolded())
    error_matrix = myunfolding.GetEmatrixTotal("error_matrix")

    hcorrelations = myunfolding.GetRhoItotal("hcorrelations")
    htruth = myunfolding.truth
    hmatrix = asrootpy(myunfolding.matrix)
    hmeasured = asrootpy(myunfolding.measured)

    hgenerated = hmatrix.ProjectionY()
    hgenerated.SetName('hgenerated')
    hreconstructed = hmatrix.ProjectionX()
    hreconstructed.SetName('hreconstructed')

    #hdifference = hdata_unfolded - hgenerated
    #hdifference.SetName('hdifference')

    #hdifference_refolded = hdata_refolded - hreconstructed
    #hdifference_refolded.SetName('hdifference_refolded')

    numexp = 10
    myunfolding.unfoldingparam = 10
    #uncertainty10 = myunfolding.StatTest(numexp)

    with rootpy.io.root_open('result_unfolding.root','recreate') as outfile:
        hdata.Write()
        hdata_unfolded.Write()
        hdata_refolded.Write()
        error_matrix.Write()
        hcorrelations.Write() 
        myunfolding.truth.Write()
        myunfolding.measured.Write()
        myunfolding.matrix.Write()
        #hdifference.Write()
        hgenerated.Write()
        hreconstructed.Write()
        #hdifference_refolded.Write()
        #uncertainty10.Write()
        outfile.Write()

if __name__ == '__main__':
    testUnfolding()
