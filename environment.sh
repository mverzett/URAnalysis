#!/bin/bash 

# Setup the environment for the framework
export URA=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P)
echo "Setting variable \$URA=$URA"
export URA_BASE=$(dirname $URA)

if [ -d "$URA_BASE/../.SCRAM" ]; then
    echo "Setting up CMSSW runtime environment"
    eval `scramv1 runtime -sh`

    #source site-dependent configuration
    source $URA/Configuration/site/site_configuration.sh
    alias crab3='/cvmfs/cms.cern.ch/crab3/crab-env-bootstrap.sh'
    export CRAB3_LOCATION=/cvmfs/cms.cern.ch/crab3/crab.sh
    export CRAB2_LOCATION=/cvmfs/cms.cern.ch/crab/crab.sh

    #re-run cmsenv, crab tends to screw up many things
    eval `scramv1 runtime -sh`

    vpython=$URA_BASE/URAnalysis/external/virtualenv
    echo "Activating python virtualenv from $vpython"

    if [ -d "$vpython" ]; then
      echo "Activating python virtual environment"
      export VIRTUAL_ENV_DISABLE_PROMPT=1
      pushd $vpython
      # See https://github.com/pypa/virtualenv/issues/150
      source bin/activate
      popd
    fi

    # Put the PWD into the PYTHONPATH
    # Make sure we prefer our virtualenv packages
    export PYTHONPATH=$vpython/lib/python2.7/site-packages/:$PYTHONPATH
else
    echo "exposing python"
    export PYTHONPATH=$URA/external:$PYTHONPATH
    $URA/install/expose_python.py
fi

# Don't require a scram build to get updated scripts
export PATH=$URA/Utilities/scripts:$PATH
export PATH=$URA/PlotTools/scripts:$PATH
export PATH=$URA/AnalysisTools/scripts:$PATH

#activate local rake
if which ruby >/dev/null && which gem >/dev/null; then
    gemsdir=$(ruby -rubygems -e 'puts Gem.user_dir')/bin
    if $(echo "$PATH"|grep -q $gemsdir) >/dev/null; then
	echo "custom ruby already sourced"
    else
	echo "activating ruby"
	PATH="$gemsdir:$PATH"
    fi
fi
