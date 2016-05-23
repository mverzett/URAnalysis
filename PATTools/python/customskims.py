import FWCore.ParameterSet.Config as cms
from pdb import set_trace

def add_skims(process, **collections):
	'''returns a list of added sequences'''
	process.hiptMuons = cms.EDFilter(
		"PATMuonSelector",
		src = cms.InputTag(collections['muons']),
		cut = cms.string('pt > 20 && abs(eta) < 2.5')
		)
	
	process.oneMuonFilter = cms.EDFilter(
	 "CandViewCountFilter",
	 src = cms.InputTag('hiptMuons'),
	 minNumber = cms.uint32(1)
	 )
	
	process.hiptElectrons = cms.EDFilter(
		"PATElectronSelector",
		src = cms.InputTag(collections['electrons']),
		cut = cms.string('pt > 20 && abs(eta) < 2.5')
		)
	
	process.oneElectronFilter = cms.EDFilter(
		"CandViewCountFilter",
		src = cms.InputTag('hiptElectrons'),
		minNumber = cms.uint32(1)
		)
	
	process.hiPtJets = cms.EDFilter(
		"PATJetSelector",
		src = cms.InputTag(collections['jets']),
		cut = cms.string('pt > 20 && abs(eta) < 10')
	)
	
	process.threeJetFilter = cms.EDFilter(
		"CandViewCountFilter",
		src = cms.InputTag('hiPtJets'),
		minNumber = cms.uint32(3)
		)
	
	process.fourJetFilter = cms.EDFilter(
		"CandViewCountFilter",
		src = cms.InputTag('hiPtJets'),
		minNumber = cms.uint32(3)
		)
	
	process.muPlus4Jets = cms.Sequence(
		process.hiptMuons *
		process.oneMuonFilter *
		process.hiPtJets *
		process.fourJetFilter
		)
	
	process.muPlus3Jets = cms.Sequence(
		process.hiptMuons *
		process.oneMuonFilter *
		process.hiPtJets *
		process.threeJetFilter
		)
	
	process.elPlus4Jets = cms.Sequence(
		process.hiptElectrons *
		process.oneElectronFilter *
		process.hiPtJets *
		process.fourJetFilter
		)
	
	process.elPlus3Jets = cms.Sequence(
		process.hiptElectrons *
		process.oneElectronFilter *
		process.hiPtJets *
		process.threeJetFilter
		)
	
	return [
		process.muPlus4Jets,
		process.muPlus3Jets,
		process.elPlus4Jets,
		process.elPlus3Jets,
		]

