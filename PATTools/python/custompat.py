import FWCore.ParameterSet.Config as cms
import URAnalysis.Utilities.cfgtools as cfgtools
from pdb import set_trace
from CondCore.DBCommon.CondDBSetup_cfi import *
try:
    #7.6.X
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetCorrFactorsUpdated
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetsUpdated
except ImportError as e:
    #8.0.X
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import updatedPatJetCorrFactors as patJetCorrFactorsUpdated
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import updatedPatJets as patJetsUpdated
from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD
from PhysicsTools.PatAlgos.tools.helpers import massSearchReplaceAnyInputTag
from URAnalysis.Utilities.version import cmssw_branch 

def preprocess(process, opts, **collections):
    '''Runs preliminary pat customization (JEC, MET corrections, etc...)
    returns the dict of final products, and the preprocessing sequence'''
    process.preprocessing = cms.Sequence()
    ##Custom database for JEC
    if opts.JECDb:
        sqfile, tag1, tag2 = tuple(opts.JECDb.split(':'))
        process.load("CondCore.DBCommon.CondDBCommon_cfi")
        process.jec = cms.ESSource(
            "PoolDBESSource",
            CondDBSetup,
            connect = cms.string('sqlite:%s' % sqfile),
            toGet = cms.VPSet(
                cms.PSet(
                    record = cms.string('JetCorrectionsRecord'),
                    tag    = cms.string(tag1), #'JetCorrectorParametersCollection_Summer15_50nsV2_MC_AK4PFchs'),
                    label  = cms.untracked.string('AK4PFchs')
                    ),
                cms.PSet(
                    record = cms.string('JetCorrectionsRecord'),
                    tag    = cms.string(tag2), #'JetCorrectorParametersCollection_Summer15_50nsV2_MC_AK4PF'),
                    label  = cms.untracked.string('AK4PF')
                    )
                )
            )
        
        ### add an es_prefer statement to resolve a possible conflict from simultaneous connection to a global tag
        process.es_prefer_jec = cms.ESPrefer('PoolDBESSource','jec')
    
    ### to re-correct the jets
    if opts.runJEC:
        process.patJetCorrFactorsReapplyJEC = patJetCorrFactorsUpdated.clone(
            src = cms.InputTag("slimmedJets"),
            levels = ['FIXME'], #to be set afterwards!
            payload = 'AK4PFchs' ) # Make sure to choose the appropriate levels and payload here!
   
        levels = cms.vstring('L1FastJet', 'L2Relative', 'L3Absolute') \
           if opts.isMC else \
           cms.vstring('L1FastJet', 'L2Relative', 'L3Absolute', 'L2L3Residual')
        process.patJetsReapplyJEC = patJetsUpdated.clone(
            jetSource = cms.InputTag("slimmedJets"),
            jetCorrFactorsSource = cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJEC"))
            )
        process.JetRecorrection = cms.Sequence(process.patJetCorrFactorsReapplyJEC + process.patJetsReapplyJEC)
        process.preprocessing *= process.JetRecorrection
        collections['jets'] = 'patJetsReapplyJEC'

        process.noHFCands = cms.EDFilter(
            "CandPtrSelector",
            src=cms.InputTag("packedPFCandidates"),
            cut=cms.string("abs(pdgId)!=1 && abs(pdgId)!=2 && abs(eta)<3.0")
            )
        #jetuncfile = 'URAnalysis/PATTools/data/Summer15_25nsV6_DATA_UncertaintySources_AK4PFchs.txt'

        runMetCorAndUncFromMiniAOD(
            process,
            #jetColl="patJetsReapplyJEC",
            isData=(not opts.isMC),
            postfix="v2"
            #,jecUncFile=jetuncfile
            )
        collections['METs'] = 'slimmedMETsv2'

        runMetCorAndUncFromMiniAOD(
            process,
            #jetColl="patJetsReapplyJEC",
            isData=(not opts.isMC),
            pfCandColl=cms.InputTag("noHFCands"),
            postfix="NoHFv2",
            #,jecUncFile=jetuncfile
            )
        collections['NoHFMETs'] = 'slimmedMETsNoHFv2'
        #bug in 7.6.X need to define levels here
        process.patJetCorrFactorsReapplyJEC.levels = levels
        #8.0.X bugfix
        if cmssw_branch() == (8,0):
            massSearchReplaceAnyInputTag(process.fullPatMetSequencev2, 'cleanedPatJets', 'cleanedPatJetsv2', verbose=True)
            massSearchReplaceAnyInputTag(process.fullPatMetSequenceNoHFv2, 'cleanedPatJets', 'cleanedPatJetsNoHFv2', verbose=True)
            massSearchReplaceAnyInputTag(process.patPFMetTxyCorrSequencev2    , 'offlinePrimaryVertices', 'offlineSlimmedPrimaryVertices', verbose=True)
            massSearchReplaceAnyInputTag(process.patPFMetTxyCorrSequenceNoHFv2, 'offlinePrimaryVertices', 'offlineSlimmedPrimaryVertices', verbose=True)
            massSearchReplaceAnyInputTag(process.patPFMetTxyCorrSequencev2    , 'particleFlow', 'packedPFCandidates', verbose=True)
            massSearchReplaceAnyInputTag(process.patPFMetTxyCorrSequenceNoHFv2, 'particleFlow', 'packedPFCandidates', verbose=True)

        if not opts.isMC:
            process.patPFMetTxyCorrv2.vertexCollection = cms.InputTag('offlineSlimmedPrimaryVertices')
            process.slimmedMETsv2.t01Variation = cms.InputTag("slimmedMETs","")
            process.patPFMetTxyCorrNoHFv2.vertexCollection = cms.InputTag('offlineSlimmedPrimaryVertices')
            process.slimmedMETsNoHFv2.t01Variation = cms.InputTag("slimmedMETsNoHF","")
            
            process.patPFMetT1T2CorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
            process.patPFMetT1T2SmearCorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
            process.patPFMetT2CorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
            process.patPFMetT2SmearCorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
        
        if hasattr(process.slimmedMETsv2, 'caloMET'): del process.slimmedMETsv2.caloMET
        if hasattr(process.slimmedMETsNoHFv2, 'caloMET'): del process.slimmedMETsNoHFv2.caloMET


    #PseudoTop
    if opts.makePSTop:
        process.load("TopQuarkAnalysis.TopEventProducers.producers.pseudoTop_cfi")
        process.pseudoTop = cms.EDProducer(
            "PseudoTopProducer",
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
        process.preprocessing *= process.pseudoTop

    return process.preprocessing, collections

def customize(process, isMC=True, **collections):
    '''Returns a tuple containing the custom PAT 
    Sequence label and final collection names'''
    #load custom objects
    #trigger is a mess, does not respect conding conventions
    #when changing something have a look at the module
    #itself
    process.load('URAnalysis.PATTools.objects.trigger')
    collections['trigger'] = 'triggerEvent'
    
    process.load('URAnalysis.PATTools.objects.vertices')
    collections['vertices'] = cfgtools.chain_sequence(
        process.customVertices,
        collections['vertices']
        )

    process.load('URAnalysis.PATTools.objects.muons')
    collections['muons'] = cfgtools.chain_sequence(
        process.customMuons,
        collections['muons']
        )
    process.muonIpInfo.vtxSrc = collections['vertices']

    process.load('URAnalysis.PATTools.objects.electrons')
    collections['electrons'] = cfgtools.chain_sequence(
        process.customElectrons,
        collections['electrons']
        )
    process.electronIpInfo.vtxSrc = collections['vertices']
    
    process.load('URAnalysis.PATTools.objects.jets')
    collections['jets'] = cfgtools.chain_sequence(
        process.customJets,
        collections['jets']
        )

    process.customPAT = cms.Sequence(
        process.customTrigger *
        process.customVertices *
        process.customMuons *
        process.customElectrons *
        process.customJets
        )

    ## if isMC:
    ##     process.load("TopQuarkAnalysis.TopEventProducers.producers.pseudoTop_cfi")
    ##     process.customPAT += process.pseudoTop
    ##     collections['PSTjets'] = 'pseudoTop:jets'
    ##     collections['PSTleptons'] = 'pseudoTop:leptons'
    ##     collections['PSTs'] = 'pseudoTop'
    ##     collections['PSTneutrinos'] = 'pseudoTop:neutrinos'

    return process.customPAT, collections
        
