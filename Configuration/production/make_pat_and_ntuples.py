#! /bin/env cmsRun

#make it executable
from URAnalysis.Configuration.varparsing import options
import FWCore.ParameterSet.Config as cms
import URAnalysis.PATTools.custompat as urpat
import URAnalysis.PATTools.customskims as urskims
import URAnalysis.PATTools.meta  as meta
import URAnalysis.Ntuplizer.ntuplizer as ntuple

options.parseArguments()

process = cms.Process("PATPlusNtuple")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = options.reportEvery
process.MessageLogger.cerr.FwkSummary.reportEvery = options.reportEvery

process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff')
process.GlobalTag.globaltag = options.globalTag

process.options = cms.untracked.PSet(
   allowUnscheduled = cms.untracked.bool(True),  
   wantSummary=cms.untracked.bool(True)
)
process.maxEvents = cms.untracked.PSet(
   input = cms.untracked.int32(
      options.maxEvents
      )
)

process.source = cms.Source(
    "PoolSource",
    # replace 'myfile.root' with the source file you want to use
    fileNames = cms.untracked.vstring(
      #'/store/relval/CMSSW_7_0_6/RelValTTbarLepton_13/MINIAODSIM/PLS170_V6AN1-v1/00000/CA50900E-43FA-E311-B663-0025905A48EC.root'
      options.inputFiles
      ),
)

process.TFileService = cms.Service(
        "TFileService",
        fileName = cms.string(options.outputFile)
)

######################
##   PREPROCESSING
######################
if options.isMC:
   from URAnalysis.Configuration.mcpreprocessing import preprocess
   collections = preprocess(process) #creates preprocessing sequence
else:
   from URAnalysis.Configuration.datapreprocessing import preprocess
   collections = preprocess(process) #creates preprocessing sequence  

#HF Noise Filter
process.load('CommonTools.RecoAlgos.HBHENoiseFilterResultProducer_cfi')
process.HBHENoiseFilterResultProducer.minZeros = cms.int32(99999) 
process.preprocessing *= process.HBHENoiseFilterResultProducer

#process.ApplyBaselineHBHENoiseFilter = cms.EDFilter('BooleanFlagFilter',
#   inputLabel = cms.InputTag('HBHENoiseFilterResultProducer','HBHENoiseFilterResult'),
#   reverseDecision = cms.bool(False)
#)

#process.load('RecoMET.METFilters.CSCTightHaloFilter_cfi')
#
#process.goodVertices = cms.EDFilter(
#  "VertexSelector",
#  filter = cms.bool(False),
#  src = cms.InputTag("offlinePrimaryVertices"),
#  cut = cms.string("!isFake && ndof > 4 && abs(z) <= 24 && position.rho < 2")
#)

if not options.noSkim:
   skim_sequences = urskims.add_skims(process, **collections)
else:
   skim_sequences = []

#store meta
process.load("Configuration.StandardSequences.Services_cff")
process.load('URAnalysis.Ntuplizer.MetaNtuplize_cfi')
process.metaTree.isMC = cms.bool(options.isMC)
process.meta = cms.Sequence(
   meta.embed_meta(process, options.isMC, options.computeWeighted and options.isMC) *
   process.metaTree
   )
process.metaTree.globalTag=process.GlobalTag.globaltag

#from pdb import set_trace
#set_trace()
#make custom PAT

custom_pat_sequence, collections = urpat.customize(
   process,
   options.isMC,
   **collections
)

ntuple_sequence, ntuple_end = ntuple.make_ntuple(
   process,
   options.isMC,
   options.computeWeighted,
   **collections
   )

process.schedule = cms.Schedule()
#make meta+skim+customPAT+Ntuple paths
#one for each skim sequence
#shared modules do not get rerun
#https://hypernews.cern.ch/HyperNews/CMS/get/edmFramework/3416/1.html

if skim_sequences:
   for skim in skim_sequences:
      path_name = skim+'Path0'
      #assure to make NEW path name
      idx = 1
      while hasattr(process, path_name):
         path_name = path_name[:-1]+str(idx)
         idx += 1
      setattr(
         process,
         path_name,
         cms.Path(
            process.meta *
            process.preprocessing *
            getattr(process, skim) *
            custom_pat_sequence *
            ntuple_sequence *
            ntuple_end
            )
         )
      process.schedule.append(
         getattr(process, path_name)
         )
else:
   process.passThroughPath = cms.Path(
      process.meta *
      process.preprocessing *
      custom_pat_sequence *
      ntuple_sequence *
      ntuple_end
      )
   process.schedule.append(process.passThroughPath)

## process.end = cms.EndPath(
##    ntuple_end
## )
## process.schedule.append(process.end)
