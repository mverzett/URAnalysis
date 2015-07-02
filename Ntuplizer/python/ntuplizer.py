import FWCore.ParameterSet.Config as cms
import URAnalysis.Ntuplizer.branches as branches
from URAnalysis.PATTools.objects.trigger import trigger_paths

def make_ntuple(process, isMC, ntuple_seq_name='ntuple', **kwargs):
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

	process.trigger = cms.EDAnalyzer(
			'NtupleTrigger',
			trigger = cms.InputTag('TriggerResults', '', 'HLT'),
			prescales = cms.InputTag('patTrigger'),
			triggerSelection = cms.vstring(trigger_paths),
			branches = cms.VPSet(
				)
			)
	ntuple += process.trigger

	process.rho = cms.EDAnalyzer(
			'NtupleDoubleProducer',
			src = cms.InputTag(
				kwargs.get(
					'rho',
					'fixedGridRhoFastjetAll'
					)
				),
			branches = cms.VPSet(
				branches.make_branch_pset('value'))
			)
	ntuple += process.rho

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
				branches.vertex_info +
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
				branches.vertex_info +
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
			'NtupleMETUncertainty',
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
		process.jets.branches.extend(branches.jet_specific_mc)
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
	
		process.MCWeights = cms.EDAnalyzer(
				'NtupleMCWeights',
				src = cms.InputTag(
					kwargs.get(
						'MCWeigths',
						'externalLHEProducer'
						)
					),
				branches = cms.VPSet(
					)
				)
		ntuple += process.MCWeights
	
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
	
		###### pseudo top test!!
		process.PSTjets = cms.EDAnalyzer(
			'NtupleGenJetsProducer',
			src = cms.InputTag(
				kwargs.get(
					'PSTjets',
					'pseudoTop:jets'
					)
				),
			branches = cms.VPSet(
				branches.kinematics +
				branches.genjet_specific
				)
			)
		ntuple += process.PSTjets
	
		process.PSTleptons = cms.EDAnalyzer(
				'NtupleGenJetsProducer',
				src = cms.InputTag(
					kwargs.get(
						'PSTleptons',
						'pseudoTop:leptons'
						)
					),
				branches = cms.VPSet(
					branches.kinematics +
					branches.genjet_specific
					)
				)
		ntuple += process.PSTleptons
	
	
		process.PSTs = cms.EDAnalyzer(
				'NtupleGenParticlesProducer',
				src = cms.InputTag(
					kwargs.get(
						'PSTs',
						'pseudoTop'
						)
					),
				branches = cms.VPSet(
					branches.kinematics +
					branches.gen_particle_specific
					)
				)
		ntuple += process.PSTs
	
		process.PSTneutrinos = cms.EDAnalyzer(
				'NtupleGenParticlesProducer',
				src = cms.InputTag(
					kwargs.get(
						'PSTneutrinos',
						'pseudoTop:neutrinos'
						)
					),
				branches = cms.VPSet(
					branches.kinematics +
					branches.gen_particle_specific
					)
				)
		ntuple += process.PSTneutrinos
	
		process.genPInheritance = cms.EDAnalyzer(
				'NtupleGenParticleInheritance',
				label = cms.string('genParticles'),
				src = cms.InputTag('prunedGenParticles'),
				)
		ntuple += process.genPInheritance
	
		process.genjets = cms.EDAnalyzer(
				'NtupleGenJetsProducer',
				src = cms.InputTag(
					kwargs.get(
						'genjets',
						'slimmedGenJets'
						)
					),
				branches = cms.VPSet(
					branches.kinematics +
					branches.genjet_specific
					)
				)
		ntuple += process.genjets
		
	process.ntupleEnd = cms.EDAnalyzer('TreeFiller')
	return ntuple, process.ntupleEnd
