import FWCore.ParameterSet.Config as cms

def skim(process, **collections):
   process.hiptElectrons = cms.EDFilter(
      "PATElectronSelector",
      src = cms.InputTag(collections['electrons']),
      cut = cms.string('pt > 20 && abs(eta) < 2.5')
      )

   process.electronFilter = cms.EDFilter(
      "CandViewCountFilter",
      src = cms.InputTag('hiptElectrons'),
      minNumber = cms.uint32(1)
      )

   process.hiPtJets = cms.EDFilter(
      "PATJetSelector",
      src = cms.InputTag(collections['jets']),
      cut = cms.string('pt > 20 && abs(eta) < 4')
      )

   process.jetFilter = cms.EDFilter(
      "CandViewCountFilter",
      src = cms.InputTag('hiPtJets'),
      minNumber = cms.uint32(3)
      )

   process.ttbarToElJets = cms.Sequence(
      process.hiptElectrons *
      process.electronFilter *
      process.hiPtJets *
      process.jetFilter
      )
   return process.ttbarToElJets.label_()
