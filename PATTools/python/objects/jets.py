import FWCore.ParameterSet.Config as cms

## from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetCorrFactorsUpdated, patJetsUpdated
## patJetCorrFactorsReapplyJEC = patJetCorrFactorsUpdated.clone(
##   src = cms.InputTag("fixme"),
##   levels = ['L1FastJet', 
##         'L2Relative', 
##         'L3Absolute'],
##   payload = 'AK4PFchs' ) # Make sure to choose the appropriate levels and payload here!
## 
## patJetsReapplyJEC = patJetsUpdated.clone(
##    jetSource = cms.InputTag("fixme"),
##    jetCorrFactorsSource = cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJEC"))
##    )

urSkimmedJets = cms.EDFilter(
    "PATJetSelector",
    src = cms.InputTag("fixme"),
    cut = cms.string('pt > 20 && abs(eta) < 4')
)

customJets = cms.Sequence(
##    patJetCorrFactorsReapplyJEC *
##    patJetsReapplyJEC *
   urSkimmedJets
)
