import FWCore.ParameterSet.Config as cms

def preprocess(process):
   '''pre-processing function for MC'''
   ################
   #Database for JEC
   process.load("CondCore.DBCommon.CondDBCommon_cfi")
   from CondCore.DBCommon.CondDBSetup_cfi import *
   process.jec = cms.ESSource("PoolDBESSource",
         CondDBSetup,
         connect = cms.string('sqlite:Summer15_25nsV6_DATA.db'),
         toGet = cms.VPSet(
         cms.PSet(
               record = cms.string('JetCorrectionsRecord'),
               tag    = cms.string('JetCorrectorParametersCollection_Summer15_25nsV6_DATA_AK4PFchs'),
               label  = cms.untracked.string('AK4PFchs')
               ),
         cms.PSet(
               record = cms.string('JetCorrectionsRecord'),
               tag    = cms.string('JetCorrectorParametersCollection_Summer15_25nsV6_DATA_AK4PF'),
               label  = cms.untracked.string('AK4PF')
               )
         )
   )
   # add an es_prefer statement to resolve a possible conflict from simultaneous connection to a global tag
   process.es_prefer_jec = cms.ESPrefer('PoolDBESSource','jec')

   ##to re-correct the jets
   from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetCorrFactorsUpdated
   process.patJetCorrFactorsReapplyJEC = patJetCorrFactorsUpdated.clone(
     src = cms.InputTag("slimmedJets"),
     levels = [
         'L1FastJet', 
         'L2Relative', 
         'L3Absolute',
         'L2L3Residual'],
     payload = 'AK4PFchs' ) # Make sure to choose the appropriate levels and payload here!

   from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetsUpdated
   process.patJetsReapplyJEC = patJetsUpdated.clone(
     jetSource = cms.InputTag("slimmedJets"),
     jetCorrFactorsSource = cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJEC"))
     )

   process.JetRecorrection = cms.Sequence(process.patJetCorrFactorsReapplyJEC + process.patJetsReapplyJEC)
   #############

   #############
   #MET without HF
   #
   #
   #
   process.noHFCands = cms.EDFilter(
      "CandPtrSelector",
      src=cms.InputTag("packedPFCandidates"),
      cut=cms.string("abs(pdgId)!=1 && abs(pdgId)!=2 && abs(eta)<3.0")
      )
   isdata = True
   #jetuncfile = 'CondFormats/JetMETObjects/data/Summer15_50nsV5_DATA_UncertaintySources_AK4PFchs.txt'
   #jetuncfile = 'CondFormats/JetMETObjects/data/Summer15_25nsV5_DATA_UncertaintySources_AK4PFchs.txt'
   jetuncfile = 'URAnalysis/PATTools/data/Summer15_25nsV6_DATA_UncertaintySources_AK4PFchs.txt'

   from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD
   runMetCorAndUncFromMiniAOD(
      process,
      jetColl="patJetsReapplyJEC",
      isData=isdata,
      postfix="v2",
      jecUncFile=jetuncfile,
      )
   process.patPFMetTxyCorrv2.vertexCollection = cms.InputTag('offlineSlimmedPrimaryVertices')
   #process.slimmedMETsv2.t01Variation = cms.InputTag("slimmedMETs","","RECO")
   process.slimmedMETsv2.t01Variation = cms.InputTag("slimmedMETs","","PAT")

   runMetCorAndUncFromMiniAOD(
      process,
      jetColl="patJetsReapplyJEC",
      isData=isdata,
      pfCandColl=cms.InputTag("noHFCands"),
      postfix="NoHFv2",
      jecUncFile=jetuncfile,
      )
   process.patPFMetTxyCorrNoHFv2.vertexCollection = cms.InputTag('offlineSlimmedPrimaryVertices')
   process.slimmedMETsNoHFv2.t01Variation = cms.InputTag("slimmedMETsNoHF","","PAT")
   #
   #process.patPFMetT1T2Corrv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
   #process.patPFMetT1T2SmearCorrv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
   #process.patPFMetT2Corrv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
   #process.patPFMetT2SmearCorrv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
   #process.shiftedPatJetEnDownv2.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
   #process.shiftedPatJetEnUpv2.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")

   process.patPFMetT1T2CorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
   process.patPFMetT1T2SmearCorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
   process.patPFMetT2CorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
   process.patPFMetT2SmearCorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")

   del getattr(process,"slimmedMETsv2").caloMET
   del getattr(process,"slimmedMETsNoHFv2").caloMET

   
   ###################################
   #      THIS HAS TO BE ALWAYS KEPT!
   ###################################
   process.preprocessing = cms.Sequence()
   collections = {
      'muons' : 'slimmedMuons',
      'electrons' : 'slimmedElectrons',
      'photons' : 'slimmedPhotons',
      'jets' : 'slimmedJets' if not hasattr(process, 'patJetsReapplyJEC') else 'patJetsReapplyJEC',
      'vertices' : 'offlineSlimmedPrimaryVertices',
      'METs' : 'slimmedMETs' if not hasattr(process, 'slimmedMETsv2')  else 'slimmedMETsv2',
      'NoHFMETs' : 'slimmedMETsNoHF' if not hasattr(process, 'slimmedMETsNoHFv2')  else 'slimmedMETsNoHFv2',
      'genParticles' : 'prunedGenParticles',
      }
   return collections

