import FWCore.ParameterSet.Config as cms

def preprocess(process):
   '''pre-processing function for MC'''
   ################
   ##Database for JEC
   #process.load("CondCore.DBCommon.CondDBCommon_cfi")
   #from CondCore.DBCommon.CondDBSetup_cfi import *
   #process.jec = cms.ESSource("PoolDBESSource",
   #      CondDBSetup,
   #      connect = cms.string('sqlite:Summer15_50nsV2_MC.db'),
   #      toGet = cms.VPSet(
   #      cms.PSet(
   #            record = cms.string('JetCorrectionsRecord'),
   #            tag    = cms.string('JetCorrectorParametersCollection_Summer15_50nsV2_MC_AK4PFchs'),
   #            label  = cms.untracked.string('AK4PFchs')
   #            ),
   #      cms.PSet(
   #            record = cms.string('JetCorrectionsRecord'),
   #            tag    = cms.string('JetCorrectorParametersCollection_Summer15_50nsV2_MC_AK4PF'),
   #            label  = cms.untracked.string('AK4PF')
   #            )
   #      )
   #)
   ### add an es_prefer statement to resolve a possible conflict from simultaneous connection to a global tag
   #process.es_prefer_jec = cms.ESPrefer('PoolDBESSource','jec')

   ###to re-correct the jets
   #from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetCorrFactorsUpdated
   #process.patJetCorrFactorsReapplyJEC = patJetCorrFactorsUpdated.clone(
   #  src = cms.InputTag("slimmedJets"),
   #  levels = ['L1FastJet', 
   #        'L2Relative', 
   #        'L3Absolute'],
   #  payload = 'AK4PFchs' ) # Make sure to choose the appropriate levels and payload here!
   #
   #from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetsUpdated
   #process.patJetsReapplyJEC = patJetsUpdated.clone(
   #  jetSource = cms.InputTag("slimmedJets"),
   #  jetCorrFactorsSource = cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJEC"))
   #  )
   #
   #process.JetRecorrection = cms.Sequence(process.patJetCorrFactorsReapplyJEC + process.patJetsReapplyJEC)
   ##############

   ##############
   #MET without HF
   #
   #
   #
   #process.noHFCands = cms.EDFilter("CandPtrSelector",
   #                                     src=cms.InputTag("packedPFCandidates"),
   #                                     cut=cms.string("abs(pdgId)!=1 && abs(pdgId)!=2 && abs(eta)<3.0")
   #                                     )
   #
   #runOnData = False 
   #from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD
   #runMetCorAndUncFromMiniAOD(process,
   #                           isData=runOnData,
   #                           )
   #
   #runMetCorAndUncFromMiniAOD(process,
   #                           isData=runOnData,
   #                           pfCandColl=cms.InputTag("noHFCands"),
   #                           postfix="NoHF"
   #                           )
   #
   #
   #process.noHFMet = cms.Sequence(process.noHFPFObjects * process.pfMet * process.corrPfMetType1 * process.noHFPFMetT1 )
   ##############

   process.load("TopQuarkAnalysis.TopEventProducers.producers.pseudoTop_cfi")
   process.pseudoTop = cms.EDProducer("PseudoTopProducer",
       genParticles = cms.InputTag("prunedGenParticles"),
       finalStates = cms.InputTag("packedGenParticles"),
       leptonMinPt = cms.double(20),
       leptonMaxEta = cms.double(2.5),
       jetMinPt = cms.double(20),
       jetMaxEta = cms.double(2.5),
       leptonConeSize = cms.double(0.1),
       jetConeSize = cms.double(0.4),
       wMass = cms.double(80.4),
       tMass = cms.double(172.5),
   )

   ###################################
   #      THIS HAS TO BE ALWAYS KEPT!
   ###################################

   process.preprocessing = cms.Sequence(process.pseudoTop)
   collections = { 
      'muons' : 'slimmedMuons',
      'electrons' : 'slimmedElectrons',
      'photons' : 'slimmedPhotons',
      'jets' : 'slimmedJets' if not hasattr(process, 'patJetsReapplyJEC') else 'patJetsReapplyJEC',
      #'jets' : 'patJetsReapplyJEC',
      'vertices' : 'offlineSlimmedPrimaryVertices',
      'METs' : 'slimmedMETs',
      'NoHFMETs' : 'slimmedMETsNoHF' if not hasattr(process, 'noHFMet') else 'noHFMet',
      #'noHFMETs' : 'noHFMet',
      'genParticles' : 'prunedGenParticles',
   }
   return collections
