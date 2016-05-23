#! /bin/env bash
set -o nounset
set -o errexit

infile=/store/mc/RunIISpring16MiniAODv1/TTToSemiLeptonic_13TeV-powheg/MINIAODSIM/PUSpring16_80X_mcRun2_asymptotic_2016_v3_ext1-v1/00000/00444E2F-160E-E611-AB57-0CC47A4D760C.root

cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=True maxEvents=100 runJEC=True globalTag=80X_mcRun2_asymptotic_2016_v3
cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=True maxEvents=100 runJEC=False globalTag=80X_mcRun2_asymptotic_2016_v3
cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=False maxEvents=100 runJEC=True globalTag=80X_mcRun2_asymptotic_2016_v3 computeWeighted=False
cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=False maxEvents=100 runJEC=False globalTag=80X_mcRun2_asymptotic_2016_v3 computeWeighted=False
cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=True maxEvents=100 makePSTop=True globalTag=80X_mcRun2_asymptotic_2016_v3
cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=True maxEvents=100 noSkim=True globalTag=80X_mcRun2_asymptotic_2016_v3
#cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=True maxEvents=100 runJEC=True globalTag=80X_mcRun2_asymptotic_2016_v3 JECDb=
cmsRun  make_pat_and_ntuples.py inputFiles=$infile isMC=True maxEvents=100 storeLHEParticles=True globalTag=80X_mcRun2_asymptotic_2016_v3
