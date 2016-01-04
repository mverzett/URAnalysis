import FWCore.ParameterSet.Config as cms
import URAnalysis.Utilities.version as version
import time

metaTree = cms.EDAnalyzer(
    'MetaNtuplizer',
    isMC=cms.bool(False),
    weightsSrc = cms.InputTag('externalLHEProducer'),
    commit=cms.string( version.git_version()),
    user=cms.string(   version.get_user()),
    cmsswVersion= cms.string( version.cmssw_version()),
    date=cms.string(time.strftime("%d %b %Y %H:%M:%S +0000", time.gmtime())),
    globalTag=cms.string('')
)
