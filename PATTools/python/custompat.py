import FWCore.ParameterSet.Config as cms
import URAnalysis.Utilities.cfgtools as cfgtools
from pdb import set_trace

def customize(process, isMC=True, **collections):
    '''Returns a tuple containing the custom PAT 
    Sequence label and final collection names'''
    #load custom objects
    #trigger is a mess, does not respect conding conventions
    #when changing something have a look at the module
    #itself
    process.load('URAnalysis.PATTools.objects.trigger')

    process.load('URAnalysis.PATTools.objects.muons')
    collections['muons'] = cfgtools.chain_sequence(
        process.customMuons,
        collections['muons']
        )
    
    process.load('URAnalysis.PATTools.objects.electrons')
    collections['electrons'] = cfgtools.chain_sequence(
        process.customElectrons,
        collections['electrons']
        )
    
    process.load('URAnalysis.PATTools.objects.jets')
    collections['jets'] = cfgtools.chain_sequence(
        process.customJets,
        collections['jets']
        )

    process.customPAT = cms.Sequence(
        process.customTrigger *
        process.customMuons *
        process.customElectrons *
        process.customJets
        )

    return process.customPAT, collections
        
