#! /usr/bin/env python

from pdb import set_trace
from URAnalysis.Utilities.rootbindings import ROOT
import math
import numpy.random
import rootpy.io
from rootpy import asrootpy
#import rootpy.plotting

from rootpy import log
log = log["/URUnfolding"]
rootpy.log.basic_config_colorized()
ROOT.TH1.AddDirectory(False)

class URUnfolding():
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
        self.dunfoldingdone = False
        self.unfoldingparam = 0.1
        self.scale = scale
        
        self.distribution = distribution
        self.truthfilename = truthfilename
        self.measuredfilename = measuredfilename
        
        self.orientation = orientation
        self.regmode = regmode
        self.constraint = constraint
        self.density = density
        
    def InitUnfolder(self):
        log.warning("Setting underflow and overflow bins to zero! This must be removed once the binning is corrected.")

        #set_trace()
        for ix in range(0,self.matrix.GetNbinsX()+1):
            self.matrix.SetBinContent(ix,0,0)
            self.matrix.SetBinContent(ix,self.matrix.GetNbinsY()+1,0)
        for iy in range(0,self.matrix.GetNbinsY()+1):
            self.matrix.SetBinContent(0,iy,0)  
            self.matrix.SetBinContent(self.matrix.GetNbinsX()+1,iy,0)
        
        self.ScaleDistributions(self.scale)

        self.unfolder = ROOT.TUnfoldDensity(
            self.matrix,
            URUnfolding.orientations[self.orientation],
            URUnfolding.regularizations[self.regmode],
            URUnfolding.constraints[self.constraint],
            URUnfolding.densities[self.density])
        
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
            status = self.unfolder.SetInput(self.measured)
            if status >= 10000:
                raise RuntimeError('Unfolding status %i. Unfolding impossible!'%status)
            self.unfolder.DoUnfold(unfoldingparam)
            self.unfoldingdone = True
        
    def DoScanTau(self):
        pass

    def DoScanLcurve(self):
        pass

    def GetUnfolded(self, unfoldingparam = None):
        self.DoUnfolding(unfoldingparam)
        return self.unfolder.GetOutput("Unfolded")

    def GetRefolded(self):
        if self.unfoldingdone == False:
            self.DoUnfolding()
        return self.unfolder.GetFoldedOutput("Refolded")

    def GetEmatrixTotal(self, name):
        if self.unfoldingdone == False:
            self.DoUnfolding()
        return self.unfolder.GetEmatrixTotal(name)

    def GetRhoItotal(self, name):
        if self.unfoldingdone == False:
            self.DoUnfolding()
        return self.unfolder.GetRhoItotal(name)

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


def testUnfolding(datafile = '', hist = ''):
    responsefile = '/uscms/home/mgalanti/nobackup/URAnalysis/CMSSW_7_2_3_patch1/src/URAnalysis/ttJets_pu30.root'
    datafile = responsefile # Need to run on a datafile different from the responsefile!
    # datafile = '/uscms/home/mgalanti/nobackup/URAnalysis/CMSSW_7_2_3_patch1/src/URAnalysis/AnalysisTools/python/unfolding/ptthad.harvested.root'
    hist = 'toppthad'
    scale = 5000.*806./13977743. # NO idea yet what this means
    scale = 1.
    myunfolding = URUnfolding(truthfilename=responsefile, measuredfilename=datafile, distribution=hist, scale=scale )
    myunfolding.LoadMatrix(distribution = myunfolding.distribution)
    myunfolding.LoadTruth(distribution = myunfolding.distribution)
    myunfolding.LoadMeasured(distribution = myunfolding.distribution)
    # myunfolding.LoadMeasured(distribution = 'tt_right', basename = '', suffix='', filedir = 'ptthad')
    myunfolding.InitUnfolder()
    # fdata = rootpy.io.root_open(datafile, 'read')
    # hdata = getattr(fdata,'fitsum') # This was the original line defining hdata
    hdata = asrootpy(myunfolding.measured) # Duplicate. Remove!
    hdata_unfolded = asrootpy(myunfolding.GetUnfolded(0.3))
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

    hdifference = hdata_unfolded - hgenerated
    hdifference.SetName('hdifference')

    hdifference_refolded = hdata_refolded - hreconstructed
    hdifference_refolded.SetName('hdifference_refolded')

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
        hdifference.Write()
        hgenerated.Write()
        hreconstructed.Write()
        hdifference_refolded.Write()
        #uncertainty10.Write()
        outfile.Write()

if __name__ == '__main__':
    testUnfolding()
