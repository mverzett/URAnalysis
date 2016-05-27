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

	## to re-correct the jets
	if opts.runJEC:
		process.patJetCorrFactorsReapplyJEC = patJetCorrFactorsUpdated.clone(
			src = cms.InputTag("slimmedJets"),
			levels = ['FIXME'], #to be set afterwards!
			payload = 'AK4PFchs'  # Make sure to choose the appropriate levels and payload here!
			)
		
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
		#handle different behaviour of 7.6 and 8.0 in a single branch
		met_kwargs = {
			'isData' : (not opts.isMC),
      'postfix' : "v2"
			}
		jetuncfile = None
		if cmssw_branch() == (7,6): 			
			met_kwargs['jetColl'] = 'patJetsReapplyJEC'
			#met_kwargs['jecUncFile'] = 'URAnalysis/PATTools/data/Summer15_25nsV6_DATA_UncertaintySources_AK4PFchs.txt'

		if not opts.useHFMET:
			runMetCorAndUncFromMiniAOD(
				process,
				**met_kwargs
				)
			collections['METs'] = 'slimmedMETsv2'
			if hasattr(process.slimmedMETsv2, 'caloMET'): del process.slimmedMETsv2.caloMET
		else:
			met_kwargs['postfix'] = 'NoHFv2'
			met_kwargs['pfCandColl'] = cms.InputTag("noHFCands")
			runMetCorAndUncFromMiniAOD(
				process,
				**met_kwargs
				)
			collections['NoHFMETs'] = 'slimmedMETsNoHFv2'
			if hasattr(process.slimmedMETsNoHFv2, 'caloMET'): del process.slimmedMETsNoHFv2.caloMET
		
		#bug in 7.6.X need to define levels here
		process.patJetCorrFactorsReapplyJEC.levels = levels
		
		if cmssw_branch() == (8,0): #8.0.X bugfix (do they ever get it right)?			
			massSearchReplaceAnyInputTag(
				getattr(process, 'fullPatMetSequence%s' % met_kwargs['postfix']), 
				'cleanedPatJets', 'cleanedPatJets%s' % met_kwargs['postfix'], verbose=True
				)
			massSearchReplaceAnyInputTag(
				getattr(process, 'patPFMetTxyCorrSequence%s' % met_kwargs['postfix']),
				'offlinePrimaryVertices', 'offlineSlimmedPrimaryVertices', verbose=True
				)
			massSearchReplaceAnyInputTag(
				getattr(process, 'patPFMetTxyCorrSequence%s' % met_kwargs['postfix']), 
				'particleFlow', 'packedPFCandidates', verbose=True
				)
		elif cmssw_branch() == (7,6): #7.6 bugfixes (do they ever get it right)?
			process.allTheFuckingMET = cms.Sequence()
			for i in dir(process):
				if i.endswith(met_kwargs['postfix']) and not isinstance(getattr(process, i), cms.Sequence):
					process.allTheFuckingMET += getattr(process, i)
			massSearchReplaceAnyInputTag(process.allTheFuckingMET, 'slimmedJets', cms.InputTag('patJetsReapplyJEC', '', process.name_()), True)
			getattr(process, 'slimmedMETs%s' % met_kwargs['postfix']).t1Uncertainties = \
				 cms.InputTag('patPFMetT1%s' % met_kwargs['postfix'], '', process.name_())			
			massSearchReplaceAnyInputTag(
				getattr(process, 'patPFMetTxyCorrSequence%s' % met_kwargs['postfix']),
				'offlinePrimaryVertices', 'offlineSlimmedPrimaryVertices', verbose=True
				)
			massSearchReplaceAnyInputTag(
				getattr(process, 'patPFMetTxyCorrSequence%s' % met_kwargs['postfix']), 
				'particleFlow', 'packedPFCandidates', verbose=True
				)			
			process.selectedPatJetsv2.src = cms.InputTag('patJetsReapplyJEC', '', process.name_())
		
		if not opts.isMC:
			getattr(process, 'patPFMetTxyCorr%s' % met_kwargs['postfix']).vertexCollection = cms.InputTag('offlineSlimmedPrimaryVertices')
			getattr(process, 'slimmedMETs%s' % met_kwargs['postfix']).t01Variation = cms.InputTag("slimmedMETs","")
			if opts.useHFMET:
				process.patPFMetT1T2CorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
				process.patPFMetT1T2SmearCorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
				process.patPFMetT2CorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
				process.patPFMetT2SmearCorrNoHFv2.jetCorrLabelRes = cms.InputTag("L3Absolute")
		
			
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
    
    import URAnalysis.PATTools.objects.jets as jets
    jet_sequence, collections['jets'] = jets.add_jets(process, collections['jets'], isMC)

    process.customPAT = cms.Sequence(
        process.customTrigger *
        process.customVertices *
        process.customMuons *
        process.customElectrons *
        jet_sequence
        )

    ## if isMC:
    ##     process.load("TopQuarkAnalysis.TopEventProducers.producers.pseudoTop_cfi")
    ##     process.customPAT += process.pseudoTop
    ##     collections['PSTjets'] = 'pseudoTop:jets'
    ##     collections['PSTleptons'] = 'pseudoTop:leptons'
    ##     collections['PSTs'] = 'pseudoTop'
    ##     collections['PSTneutrinos'] = 'pseudoTop:neutrinos'

    return process.customPAT, collections
        
