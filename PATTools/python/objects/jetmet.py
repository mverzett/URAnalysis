import FWCore.ParameterSet.Config as cms
try:
    #7.6.X
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetCorrFactorsUpdated
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetsUpdated
except ImportError as e:
    #8.0.X
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import updatedPatJetCorrFactors as patJetCorrFactorsUpdated
    from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import updatedPatJets as patJetsUpdated
from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD
from PhysicsTools.PatAlgos.tools.metTools import addMETCollection

def shift_MET(process, sequence, postfix, shiftedJets, unshifted='slimmedJetsNewJEC', metsrc='slimmedMETsNewJEC'):
	corr_name = 'shiftedMETCorrModuleFor%s' % postfix
	setattr(
		process,
		corr_name,
		cms.EDProducer(
			'ShiftedParticleMETcorrInputProducer',
			srcOriginal = cms.InputTag(unshifted),
			srcShifted = cms.InputTag(shiftedJets)
			)
		)
	sequence *= getattr(process, corr_name)

	name = 'slimmedMETs%s' % postfix
	setattr(
		process,
		name,
		cms.EDProducer(
			'CorrectedPATMETProducer',
			src = cms.InputTag(metsrc),
			srcCorrections = cms.VInputTag(cms.InputTag(corr_name))
			)
		)
	sequence *= getattr(process, name)
	return name

def rerun_JECJER(process, opts, collections):
	'I will make my own correction, with blackjack and hookers! (cit.)'
	#re-run JEC
	process.newJECJER = cms.Sequence()
	process.patJetCorrFactorsReapplyJEC = patJetCorrFactorsUpdated.clone(
		src = cms.InputTag(collections['jets']),
		levels = cms.vstring('L1FastJet', 'L2Relative', 'L3Absolute') \
			if opts.isMC else \
			cms.vstring('L1FastJet', 'L2Relative', 'L3Absolute', 'L2L3Residual'),
		payload = 'AK4PFchs'
		)
	process.patJetCorrFactorsReapplyJEC.levels = cms.vstring('L1FastJet', 'L2Relative', 'L3Absolute', 'L2L3Residual')
	process.newJECJER *= process.patJetCorrFactorsReapplyJEC
	
	process.slimmedJetsNewJEC = patJetsUpdated.clone(
		jetSource = cms.InputTag(collections['jets']),
		jetCorrFactorsSource = cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJEC"))
		)
	process.newJECJER *= process.slimmedJetsNewJEC
	collections['jets'] = 'slimmedJetsNewJEC'

	#
	# Reset MET
	#
	originalMET = collections['METs']
	if opts.isMC:
		process.genMet = cms.EDProducer(
			"GenMETExtractor",
			metSource = cms.InputTag(collections['METs'], "", "@skipCurrentProcess")
			)
		process.newJECJER *= process.genMet
	
	process.uncorrectedMet = cms.EDProducer(
		"RecoMETExtractor",
		correctionLevel = cms.string('raw'),
		metSource = cms.InputTag(collections['METs'], "", "@skipCurrentProcess")
		)
	process.newJECJER *= process.uncorrectedMet
	
	addMETCollection(process, labelName="uncorrectedPatMet", metSource="uncorrectedMet")
	if opts.isMC:
		process.uncorrectedPatMet.genMETSource = cms.InputTag('genMet')
	else:
		process.uncorrectedPatMet.addGenMET = False
	process.newJECJER *= process.uncorrectedPatMet #probably not needed since unscheduled, but fuck it
	process.Type1CorrForNewJEC = cms.EDProducer(
		"PATPFJetMETcorrInputProducer",
    src = cms.InputTag('slimmedJetsNewJEC'),
    offsetCorrLabel = cms.InputTag("L1FastJet"),
    jetCorrLabel = cms.InputTag("L3Absolute"), # for MC
    jetCorrLabelRes = cms.InputTag("L2L3Residual"), # for Data automatic switch
    type1JetPtThreshold = cms.double(15.0),
    skipEM = cms.bool(True),
    skipEMfractionThreshold = cms.double(0.90),
    skipMuons = cms.bool(True),
    skipMuonSelection = cms.string("isGlobalMuon | isStandAloneMuon")
		#WAS (in 7.6)
		#isMC = cms.bool(opts.isMC),
		#jetCorrLabel = cms.InputTag("L3Absolute"),
		#jetCorrLabelRes = cms.InputTag("L2L3Residual"),
		#offsetCorrLabel = cms.InputTag("L1FastJet"),
		#skipEM = cms.bool(True),
		#skipEMfractionThreshold = cms.double(0.9),
		#skipMuonSelection = cms.string('isGlobalMuon | isStandAloneMuon'),
		#skipMuons = cms.bool(True),
		#src = cms.InputTag("slimmedJetsNewJEC"),
		#type1JetPtThreshold = cms.double(15.0),
		#type2ExtraCorrFactor = cms.double(1.0),
		#type2ResidualCorrEtaMax = cms.double(9.9),
		#type2ResidualCorrLabel = cms.InputTag(""),
		#type2ResidualCorrOffset = cms.double(0.0)
		)
	process.newJECJER *= process.Type1CorrForNewJEC
	
	process.slimmedMETsNewJEC = cms.EDProducer(
		'CorrectedPATMETProducer',
		src = cms.InputTag('uncorrectedPatMet'),
		srcCorrections = cms.VInputTag(cms.InputTag('Type1CorrForNewJEC', 'type1'))
		)
	process.newJECJER *= process.slimmedMETsNewJEC
	collections['METs'] = 'slimmedMETsNewJEC'
	if not opts.isMC:
		return collections, 'newJECJER'
	
	
	#### Second, smear newly corrected jets	
	process.slimmedJetsSmeared = cms.EDProducer(
		'SmearedPATJetProducer',
		src = cms.InputTag('slimmedJetsNewJEC'),
		enabled = cms.bool(True),
		rho = cms.InputTag("fixedGridRhoFastjetAll"),
		# Read from GT
    algopt = cms.string('AK4PFchs_pt'),
    algo = cms.string('AK4PFchs'),
		#or from txt file (DEPRECATED!)
		#resolutionFile  = cms.FileInPath('URAnalysis/PATTools/data/Fall15_25nsV2_MC_PtResolution_AK4PFchs.txt'),
		#scaleFactorFile = cms.FileInPath('URAnalysis/PATTools/data/Fall15_25nsV2_MC_SF_AK4PFchs.txt'),
		
		genJets = cms.InputTag('slimmedGenJets'),
		dRMax = cms.double(0.2),
		dPtMaxFactor = cms.double(3),
		
		variation = cms.int32(0),
		debug = cms.untracked.bool(False)
		)
	process.newJECJER *= process.slimmedJetsSmeared
	
	METSmeared = shift_MET(process, process.newJECJER, 'Smeared', 'slimmedJetsSmeared')

	#
	# Compute shifts
	#
	# JES
	process.slimmedJetsNewJECJESUp = cms.EDProducer(
		"ShiftedPATJetProducer",
		addResidualJES = cms.bool(True),
		jetCorrLabelUpToL3 = cms.InputTag("ak4PFCHSL1FastL2L3Corrector"),
		jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3ResidualCorrector"),
		jetCorrPayloadName = cms.string('AK4PFchs'),
		jetCorrUncertaintyTag = cms.string('Uncertainty'),
		shiftBy = cms.double(1.0),
		src = cms.InputTag(collections['jets'])
		)
	process.newJECJER *= process.slimmedJetsNewJECJESUp
	METJESP = shift_MET(process, process.newJECJER, 'JESUp', 'slimmedJetsNewJECJESUp')
	
	process.slimmedJetsNewJECJESDown = process.slimmedJetsNewJECJESUp.clone(shiftBy = cms.double(-1.0))
	process.newJECJER *= process.slimmedJetsNewJECJESDown
	METJESM = shift_MET(process, process.newJECJER, 'JESDown', 'slimmedJetsNewJECJESDown')
	
	# JER
	process.slimmedJetsSmearedJERUp = process.slimmedJetsSmeared.clone(variation = cms.int32(1))
	process.newJECJER *= process.slimmedJetsSmearedJERUp
	METJERP = shift_MET(process, process.newJECJER, 'JERUp', 'slimmedJetsSmearedJERUp')

	process.slimmedJetsSmearedJERDown = process.slimmedJetsSmeared.clone(variation = cms.int32(-1))
	process.newJECJER *= process.slimmedJetsSmearedJERDown
	METJERM = shift_MET(process, process.newJECJER, 'JERDown', 'slimmedJetsSmearedJERDown')
	
	process.jetsNewJECAllEmbedded = cms.EDProducer(
		'PATJetsEmbedder',
		src = cms.InputTag(collections['jets']),
		trigMatches = cms.VInputTag(),
		trigPaths = cms.vstring(),
		floatMaps = cms.PSet(),
		shiftNames = cms.vstring('JES+', 'JES-', 'JER', 'JER+', 'JER-'),
		shiftedCollections = cms.VInputTag(
			cms.InputTag('slimmedJetsNewJECJESUp'),
			cms.InputTag('slimmedJetsNewJECJESDown'),
			cms.InputTag('slimmedJetsSmeared'),
			cms.InputTag('slimmedJetsSmearedJERUp'),
			cms.InputTag('slimmedJetsSmearedJERDown'),
			),
		)
	collections['jets'] = 'jetsNewJECAllEmbedded'
	process.newJECJER *= process.jetsNewJECAllEmbedded

	process.METsNewJECAllEmbedded = cms.EDProducer(
		'PATMETEmbedder',
		src = cms.InputTag(collections['METs']),	
		trigMatches = cms.VInputTag(),
		trigPaths = cms.vstring(),
		floatMaps = cms.PSet(),
		shiftNames = cms.vstring('ORIGINAL', 'JES+', 'JES-', 'JER', 'JER+', 'JER-'),
		shiftedCollections = cms.VInputTag(
			cms.InputTag(originalMET),
			cms.InputTag(METJESP),
			cms.InputTag(METJESM),
			cms.InputTag(METSmeared),
			cms.InputTag(METJERP),
			cms.InputTag(METJERM),
			),
		)
	collections['METs'] = 'METsNewJECAllEmbedded'
	process.newJECJER *= process.jetsNewJECAllEmbedded
	return collections, 'newJECJER'
