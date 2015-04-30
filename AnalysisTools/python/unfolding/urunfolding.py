#! /usr/bin/env python

from URAnalysis.Utilities.rootbindings import ROOT
import math
import numpy.random
import rootpy.io
import rootpy.plotting


class URUnfolding():
    def __init__(self, filename = '/uscms/home/mgalanti/nobackup/URAnalysis/CMSSW_7_2_3_patch1/src/URAnalysis/ttJets_pu30.root', distribution = 'topptlep', scale = 1.):
        self.unfoldingparam = 10
        myfile = rootpy.io.root_open(filename, 'read')
        self.hmatrix = getattr(myfile.TRUTH,'truth_response_'+distribution+'_matrix')
        self.htruth = getattr(myfile.TRUTH,'truth_response_'+distribution+'_truth')
        self.hmeasured = getattr(myfile.TRUTH,'truth_response_'+distribution+'_measured')
        print type(self.hmatrix)
        self.hmatrix.scale(scale)
        self.htruth.scale(scale)
        self.hmeasured.scale(scale)
        newfile = rootpy.io.root_open("output_prova.root", 'recreate')
        self.hmatrix.Write()
        self.htruth.Write()
        self.hmeasured.Write()
        newfile.Close()

    def GetUnfolded(self,tounfold):
        #Actual unfolding to be written! For the time being it returns the input histogram
        return tounfold

    def Generate(self, numevents):
        if (not hasattr(self,'gentruth')) or self.gentruth == 0:
            self.hmiss = ROOT.TH1D(self.htruth)
            self.hmiss.Add(self.hmatrix.ProjectionX(), -1.)
            self.hfake = ROOT.TH1D(self.hmeasured)
            self.hfake.Add(self.hmatrix.ProjectionY(), -1.)
            self.gentruth = ROOT.TH1D(self.htruth)
            self.genmeasured = ROOT.TH1D(self.htruth)
            maxima = [self.hmiss.GetMaximum(), self.hfake.GetMaximum(), self.hmatrix.GetMaximum()]
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
            if float(nev)%1000 == 0:
               print "nev =",nev
            binx = numpy.random.random_integers(0,nbinsx)
            biny = numpy.random.random_integers(0,nbinsy)
            test = numpy.random.uniform(0,self.maxval)
            if binx > 0 and biny > 0:
                dest = self.hmatrix.GetBinContent(binx, biny)
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
    hist = 'topptlep'
    scale = 5000.*806./13977743. # NO idea yet what this means
    scale = 0.001
    myunfolding = URUnfolding(responsefile, hist, scale)
    fdata = rootpy.io.root_open(datafile, 'read')
    # hdata = getattr(fdata,'fitsum') # This was the original line defining hdata
    hdata = getattr(fdata.TRUTH,'truth_response_'+hist+'_measured')
    hdata_unfolded = myunfolding.GetUnfolded(hdata)

    numexp = 10
    myunfolding.unfoldingparam = 10
    uncertainty10 = myunfolding.StatTest(numexp)

    outfile = rootpy.io.root_open('result_unfolding.root','recreate')
    hdata.Write()
    hdata_unfolded.Write()
    myunfolding.htruth.Write()
    myunfolding.hmeasured.Write()
    uncertainty10.Write()
    outfile.Write()
    outfile.Close()



 
        
