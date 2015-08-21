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
   'computeWeighted',
   True,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.bool,
   'Computed weighted number of events for MC samples'
)
options.register(
   'reportEvery',
   100,
   VarParsing.multiplicity.singleton,
   VarParsing.varType.int,
   'Verbosity of message logs'
)
