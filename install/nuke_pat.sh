#! /bin/env bash
set -o nounset
set -o errexit

pushd $CMSSW_BASE/src/URAnalysis/PATTools
find .  -type f | grep -v BuildFile | xargs rm
git ls-files . | xargs -n 1 git update-index --assume-unchanged
popd
pushd $CMSSW_BASE/src/URAnalysis/Ntuplizer
find .  -type f | grep -v BuildFile | xargs rm
git ls-files . | xargs -n 1 git update-index --assume-unchanged
popd
