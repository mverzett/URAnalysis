import FWCore.ParameterSet.Config as cms
from PhysicsTools.PatUtils.patPFMETCorrections_cff import patSmearedJets

def add_jets(process, collection, opts):
	process.urSkimmedJets = cms.EDFilter(
    "PATJetSelector",
    src = cms.InputTag(collection),
    cut = cms.string('pt > 20 && abs(eta) < 4')
		)

	process.customJets = cms.Sequence(
		process.urSkimmedJets
		)
	return process.customJets, 'urSkimmedJets'
	
	process.urSmearedSkimmedJetsJERM = process.urSmearedSkimmedJets.clone(
		shiftBy = cms.double(-1.0),
		areSrcJetsSmeared = cms.bool(False)
		)
	process.customJets *= process.urSmearedSkimmedJetsJERM
	
	process.embeddedURJets = cms.EDProducer(
		'PATJetsEmbedder',
		src = cms.InputTag('urSkimmedJets'),
		trigMatches = cms.VInputTag(),
		trigPaths = cms.vstring(),
		floatMaps = cms.PSet(),
		shiftNames = cms.vstring('JES+', 'JES-', 'JER+', 'JER-', 'JER'),
		shiftedCollections = cms.VInputTag(
			cms.InputTag('urSkimmedJetsJESP'),
			cms.InputTag('urSkimmedJetsJESM'),
			cms.InputTag('urSmearedSkimmedJetsJERP'),
			cms.InputTag('urSmearedSkimmedJetsJERM'),
			cms.InputTag('urSmearedSkimmedJets'),
			),
		)
	process.customJets *= process.embeddedURJets
	return process.customJets, 'embeddedURJets'
