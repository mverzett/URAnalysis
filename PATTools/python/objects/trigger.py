import FWCore.ParameterSet.Config as cms

###
# variables used by other modules, but here for consistency
###

trigger_paths = [
   'HLT_Ele27_eta2p1_WPLoose_Gsf',
   'HLT_DoubleIsoMu17_eta2p1',
   'HLT_notexists',
   'HLT_Ele27_WP85_Gsf',
   'HLT_IsoMu24_eta2p1',
   'HLT_IsoMu20_eta2p1',
   'HLT_DoubleEle33_CaloIdL_GsfTrkIdVL',
   'HLT_IsoMu22',
   'HLT_IsoMu18',
   'HLT_IsoTkMu20',
   'HLT_IsoMu20',
   'HLT_IsoMu27',
   'HLT_Ele27_eta2p1_WP75_Gsf',
   'HLT_Ele22_eta2p1_WP75_Gsf',
   'HLT_Ele22_eta2p1_WPLoose_Gsf',
]

#match_template = cms.EDProducer(
#   "PATTriggerMatcherDRDPtLessByR",
#   src     = cms.InputTag('urSkimmedMuons'),
#   #made in trigger.py
#   matched = cms.InputTag('unpackedPatTrigger'),
#   matchedCuts = cms.string('path("HLT_%s_v*") || type("TriggerMuon")'),
#   maxDPtRel = cms.double(0.5),
#   maxDeltaR = cms.double(0.5),
#   resolveAmbiguities    = cms.bool(True),
#   resolveByMatchQuality = cms.bool(True),
#   #ensure we do not chain it as it makes an 
#   #association map
#   noSeqChain = cms.bool(True),
#)

#unpacks trigger names, this module does not
#respect any coding convention, no src or similar,
#just leave it hardcoded and hope for the best!
from PhysicsTools.PatAlgos.slimming.unpackedPatTrigger_cfi import unpackedPatTrigger

#triggerEvent = cms.EDProducer(
#   'URTriggerProducer',
#   bits = cms.InputTag('TriggerResults::HLT'),
#   prescales = cms.InputTag('patTrigger'),
#)

customTrigger = cms.Sequence(
   unpackedPatTrigger
#   triggerEvent
)
