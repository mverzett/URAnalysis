import FWCore.ParameterSet.Config as cms

urSkimmedElectrons = cms.EDFilter(
    "PATElectronSelector",
    src = cms.InputTag("fixme"),
    cut = cms.string('pt > 15 && abs(eta) < 2.5')
)
customElectrons = cms.Sequence(
   urSkimmedElectrons
)

#trigger match
#from URAnalysis.PATTools.objects.trigger import trigger_paths, match_template

#matchers = []
#elpaths = [i for i in trigger_paths if 'Ele' in i]
#for path in elpaths:
#   matcher_name = 'matchElectrons%s' % path.replace('_','')
#   matchers.append(matcher_name)
#   globals()[matcher_name] = match_template.clone(
#      src = cms.InputTag('urSkimmedElectrons'),
#      matchedCuts = cms.string('path("HLT_%s_v*") || type("TriggerElectron")' % path)
#      )
#   customElectrons *= globals()[matcher_name]
#

electronIpInfo = cms.EDProducer(
   'PATElectronIpEmbedder',
   src = cms.InputTag('urSkimmedElectrons'),
   vtxSrc = cms.InputTag('fixme'),
   #ensure we do not chain it as it makes
   #a ValueMap
   noSeqChain = cms.bool(True),
)
customElectrons *= electronIpInfo

urElectrons = cms.EDProducer(
   'PATElectronsEmbedder',
   src = cms.InputTag('electronIpInfo'),
   trigMatches = cms.VInputTag(
#      cms.InputTag(i) for i in matchers
      ),
   trigPaths = cms.vstring(
#      elpaths
      ),
   floatMaps = cms.PSet(
      ipDXY = cms.InputTag("electronIpInfo:ipDXY"),
      dz	  = cms.InputTag("electronIpInfo:dz"	 ),
      vz	  = cms.InputTag("electronIpInfo:vz"	 ),
      ip3D  = cms.InputTag("electronIpInfo:ip3D" ),
      ip3DS = cms.InputTag("electronIpInfo:ip3DS"),
      missingInnerHits = cms.InputTag("electronIpInfo:missingInnerHits"),
      )
)
customElectrons *= urElectrons

