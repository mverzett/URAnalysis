import FWCore.ParameterSet.Config as cms
import URAnalysis.Utilities.version as version
import time

def embed_meta(process, isMC, computeWeighted):
    process.storeMeta = cms.Sequence()
    # Hack meta information about this PAT tuple in the provenance.
    global_tag = process.GlobalTag.globaltag \
        if hasattr(process, 'GlobalTag') else \
        cms.string('NOT_SET')

    process.processedEvents = cms.EDProducer(
        "EventCountProducer",
        meta = cms.PSet(
            commit=cms.string( version.git_version()),
            user=cms.string(   version.get_user()),
            cmsswVersion= cms.string( version.cmssw_version()),
            date=cms.string(time.strftime("%d %b %Y %H:%M:%S +0000", time.gmtime())),
            globalTag=global_tag,
            )
        )
    process.storeMeta += process.processedEvents

    process.weightedProcessedEvents = cms.EDProducer(
        'WeightedEventCountProducer',
        lhes = cms.InputTag('externalLHEProducer', '', 'LHE'),
        computeWeighted = cms.bool(computeWeighted)
        )
    process.storeMeta += process.weightedProcessedEvents


    if isMC:
        process.load("Configuration.StandardSequences.Services_cff")
        process.storePU = cms.EDAnalyzer(
            'PUDistributionProducer',
            binning = cms.PSet(
                nbins = cms.int32(100),
                min   = cms.double(0),
                max   = cms.double(100),
                ),
            src = cms.InputTag('slimmedAddPileupInfo')
            )
        process.storeMeta += process.storePU
        
        
    return process.storeMeta
