from FWCore.ParameterSet.VarParsing import VarParsing

options = VarParsing("analysis")
#inputFiles, outputFile, maxEvents
#options come for free in the VarParsing
options.register(
   'globalTag',
   '',
   VarParsing.multiplicity.singleton,
   VarParsing.varType.string,
   'global tag to be used'
)
options.register(
   'isMC',
   False,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Switch to MC production'
)
options.register(
   'runJEC',
   False,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Re-run JEC'
)
options.register(
   'JECDb',
   '',
   VarParsing.multiplicity.singleton,
   VarParsing.varType.string,
   'Re-run JEC with custom DB file and tag. '
   'format dbfile.db:tagAK4PFchs:tagAK4PF'
)
options.register(
   'makePSTop',
   False,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Run (and store) pseudo-top'
)
options.register(
   'useHFMET',
   False,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Run no HF MET'
)
options.register(
	'storeLHEParticles',
	False,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
	'store LHE particles'
)	
options.register(
   'makeJetTracks',
   False,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Store jet track info'
)
options.register(
   'skim',
   '',
   VarParsing.multiplicity.singleton,
   VarParsing.varType.string,
   'Set which skim to run'
)

options.register(
   'computeWeighted',
   True,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Computed weighted number of events for MC samples'
)
options.register(
   'noSkim',
   False,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Do not apply any skim to the sample'
)
options.register(
   'reportEvery',
   100,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.int,
   'Verbosity of message logs'
)
