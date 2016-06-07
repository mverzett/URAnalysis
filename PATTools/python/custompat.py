import FWCore.ParameterSet.Config as cms
import URAnalysis.Utilities.cfgtools as cfgtools
from pdb import set_trace
from CondCore.DBCommon.CondDBSetup_cfi import *
from PhysicsTools.PatAlgos.tools.helpers import massSearchReplaceAnyInputTag
from URAnalysis.Utilities.version import cmssw_branch 
from URAnalysis.PATTools.objects.jetmet import rerun_JECJER

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
		collections, seqname = rerun_JECJER(process, opts, collections)
		process.preprocessing *= getattr(process, seqname)
				
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

def customize(process, opts, **collections):
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
    jet_sequence, collections['jets'] = jets.add_jets(process, collections['jets'], opts)

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
        
