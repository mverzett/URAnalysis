#!/usr/bin/env bash

set -o errexit
set -o nounset

: ${CMSSW_BASE:?"CMSSW_BASE is not set!  Run cmsenv before recipe.sh"}

install=$CMSSW_BASE/src/URAnalysis/install
cms_src=$CMSSW_BASE/src

#add recipe to include pseudoTop code
if [ "$CMSSW_VERSION" -ne CMSSW_7_4_7 ]; then 
    echo "This install recipe is made to work in CMSSW_7_4_7, check it before running it!"
		exit 1
fi

pushd $cms_src

#installing fastHadd
echo "-------------------------------------------------------"
echo "-----          INSTALLING fastHadd         ------------"
echo "-------------------------------------------------------"
git cms-addpkg DQMServices/Components
pushd DQMServices/Components/bin
wget https://raw.githubusercontent.com/cms-sw/cmssw/CMSSW_8_1_X/DQMServices/Components/bin/fastHadd.cc
popd
sed -i 's|#include <TKey.h>|#include <TKey.h>\n#include <limits>|g' DQMServices/Components/bin/fastHadd.cc
sed -i 's|1024\*1024\*1024|std::numeric_limits<int>::max()|g' DQMServices/Components/bin/fastHadd.cc

#installing combine
echo "-------------------------------------------------------"
echo "-----          INSTALLING COMBINE          ------------"
echo "-------------------------------------------------------"
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
pushd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v6.3.0
git checkout -b combine_dev
popd

echo "-------------------------------------------------------"
echo "-----          INSTALLING COMBINEHARVESTER     --------"
echo "-------------------------------------------------------"
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
pushd CombineHarvester
git remote add jan https://github.com/steggema/CombineHarvester
git fetch jan
git checkout httbar_74
popd

popd
