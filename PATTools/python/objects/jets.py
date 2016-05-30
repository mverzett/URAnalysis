import FWCore.ParameterSet.Config as cms

def add_jets(process, collection, opts):
	process.urSkimmedJets = cms.EDFilter(
    "PATJetSelector",
    src = cms.InputTag(collection),
    cut = cms.string('pt > 20 && abs(eta) < 4')
		)

	process.customJets = cms.Sequence(
		process.urSkimmedJets
		)
	if not opts.isMC:
		return process.customJets, 'urSkimmedJets'

	process.urSkimmedJetsJESP = cms.EDProducer(
		"ShiftedPATJetProducer",
		addResidualJES = cms.bool(True),
		jetCorrLabelUpToL3 = cms.InputTag("ak4PFCHSL1FastL2L3Corrector"),
		jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3ResidualCorrector"),
		jetCorrPayloadName = cms.string('AK4PFchs'),
		jetCorrUncertaintyTag = cms.string('Uncertainty'),
		shiftBy = cms.double(1.0),
		src = cms.InputTag("urSkimmedJets")
		)
	process.customJets *= process.urSkimmedJetsJESP

	process.urSkimmedJetsJESM = cms.EDProducer(
		"ShiftedPATJetProducer",
		addResidualJES = cms.bool(True),
		jetCorrLabelUpToL3 = cms.InputTag("ak4PFCHSL1FastL2L3Corrector"),
		jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3ResidualCorrector"),
		jetCorrPayloadName = cms.string('AK4PFchs'),
		jetCorrUncertaintyTag = cms.string('Uncertainty'),
		shiftBy = cms.double(-1.0),
		src = cms.InputTag("urSkimmedJets")
		)
	process.customJets *= process.urSkimmedJetsJESM
	#if opts.JECUnc:
	#	process.urSkimmedJetsJESP = process.shiftedPatJetEnUpv2.clone()
	#	process.urSkimmedJetsJESM = process.shiftedPatJetEnDownv2.clone()
	#	process.urSkimmedJetsJESP.jetCorrInputFileName = cms.FileInPath(opts.JECUnc)
	#	process.urSkimmedJetsJESM.jetCorrInputFileName = cms.FileInPath(opts.JECUnc)
	
	process.embeddedURJets = cms.EDProducer(
		'PATJetsEmbedder',
		src = cms.InputTag('urSkimmedJets'),
		trigMatches = cms.VInputTag(),
		trigPaths = cms.vstring(),
		floatMaps = cms.PSet(),
		shiftNames = cms.vstring('JES+', 'JES-'),
		shiftedCollections = cms.VInputTag(
			cms.InputTag('urSkimmedJetsJESP'),
			cms.InputTag('urSkimmedJetsJESM')
			),
		)
	process.customJets *= process.embeddedURJets
	return process.customJets, 'embeddedURJets'
