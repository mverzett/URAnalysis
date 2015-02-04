import FWCore.ParameterSet.Config as cms
import URAnalysis.Ntuplizer.branches as branches

def make_ntuple(
   process, isMC, ntuple_seq_name='ntuple', **kwargs):
   '''
   Function to customize the process and add the Ntuple
   production sequence as ntuple_seq_name (default 'ntuple').
   keyword args can be passed to modify the source of each
   Ntuple object, the keyword is the ntuple object name
   returns a tuple: (ntuple_sequence, ntuple_end_module)
   '''
   if not hasattr(process, ntuple_seq_name):
      setattr(process, ntuple_seq_name, cms.Sequence())

   ntuple = getattr(process, ntuple_seq_name)
   if not isinstance(ntuple, cms.Sequence):
      raise ValueError(
         'The process already has module named '
         '"ntuple", which is not a cms.Sequence, '
         'please choose a different name while builing'
         'the ntuple'
         )

   process.evtid = cms.EDAnalyzer(
      'EvtIDProducer'
      )
   ntuple += process.evtid

   if 'trigger' in kwargs:
      process.trigger = cms.EDAnalyzer(
         'NtupleTriggerEventProducer',
         src = cms.InputTag(
            kwargs['trigger']
            ),
         branches = cms.VPSet(
            branches.trigger)
         )
      ntuple += process.trigger

   process.muons = cms.EDAnalyzer(
      'NtupleMuonsProducer',
      src = cms.InputTag(
         kwargs.get(
            'muons', 
            'slimmedMuons'
            )
         ),
      branches = cms.VPSet(
         branches.kinematics +
         branches.isolation +
         branches.muon_specific
         )
   )
   ntuple += process.muons

   process.jets = cms.EDAnalyzer(
      'NtupleJetsProducer',
      src = cms.InputTag(
         kwargs.get(
            'jets',
            'slimmedJets'
            )
         ),
      branches = cms.VPSet(
         branches.kinematics +
         branches.jet_specific +
         branches.btaggging
         )
   )
   ntuple += process.jets

   process.electrons = cms.EDAnalyzer(
      'NtupleElectronsProducer',
      src = cms.InputTag(
            kwargs.get(
               'electrons',
               'slimmedElectrons'
               )
            ),
      branches = cms.VPSet(
         branches.kinematics +
         branches.isolation +
         branches.electron_specific +
         branches.ecal_cluster_specific + 
         branches.super_cluster_specific
         )
   )
   ntuple += process.electrons

   process.photons = cms.EDAnalyzer(
      'NtuplePhotonsProducer',
      src = cms.InputTag(
         kwargs.get(
            'photons',
            'slimmedPhotons'
            )
         ),
      branches = cms.VPSet(
         branches.kinematics +
         branches.super_cluster_specific +
         branches.photon_specific
         )
   )
   ntuple += process.photons

   process.vertexs = cms.EDAnalyzer(
      'NtupleVerticesProducer',
      src = cms.InputTag(
         kwargs.get(
            'vertexs',
            'offlineSlimmedPrimaryVertices'
            )
         ),
      branches = cms.VPSet(
         branches.vertex_specific
         )
   )
   ntuple += process.vertexs

   process.METs = cms.EDAnalyzer(
      'NtupleMETProducer',
      src = cms.InputTag(
         kwargs.get(
            'METs',
            'slimmedMETs'
            )
         ),
      branches = cms.VPSet(
         branches.met_specific
         )
   )
   ntuple += process.METs

   #############
   #  MC Only
   #############
   if isMC:
     #FIXME: add it!
     process.genInfo = cms.EDAnalyzer(
        'NtupleGenInfoProducer',
        src = cms.InputTag(
           kwargs.get(
              'genInfo',
              'generator'
              )
           ),
        branches = cms.VPSet(
           branches.geninfo_scpecific
           )
     )
     ntuple += process.genInfo

     process.PUInfos = cms.EDAnalyzer(
        'NtuplePUInfoProducer',
        src = cms.InputTag(
           kwargs.get(
              'PUInfos',
              'addPileupInfo'
              )
           ),
        branches = cms.VPSet(
           branches.puinfo_specific
           )
     )
     ntuple += process.PUInfos

     #genMET = cms.EDAnalyzer(
     process.genParticles = cms.EDAnalyzer(
        'NtupleGenParticlesProducer',
        src = cms.InputTag(
           kwargs.get(
              'genParticles',
              'prunedGenParticles'
              )
           ),
        branches = cms.VPSet(
           branches.kinematics +
           branches.gen_particle_specific
           )
     )
     ntuple += process.genParticles

     process.genPInheritance = cms.EDAnalyzer(
        'NtupleGenParticleInheritance',
        label = cms.string('genParticles'),
        src = cms.InputTag('prunedGenParticles'),
     )
     ntuple += process.genPInheritance

   process.ntupleEnd = cms.EDAnalyzer('TreeFiller')
   return ntuple, process.ntupleEnd
