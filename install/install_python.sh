#! /bin/env bash

#
# Installs python virtualenv to allow control over installed packages
#
# Author: Mauro Verzetti, UR
#

fwk_location=$CMSSW_BASE/src/URAnalysis
external=$fwk_location/external
vpython=$external/virtualenv
vpython_src=$external/src/virtualenv

pushd $vpython_src

echo "Creating virtual python environment in $vpython"
if [ ! -d "$vpython" ]; then
  ./virtualenv.py --distribute $vpython
else
  echo "...virtual environment already setup."
fi

popd

echo "Activating virtual python environment"
pushd $vpython
source bin/activate

echo "Installing yolk -- python package management"
pip install -U yolk
echo "Installing ipython -- better interactive python"
pip install -U ipython
#echo "Installing termcolor -- colors terminal"
#pip install -U termcolor
echo "Installing uncertainties -- awesome error propagation package"
pip install -U uncertainties
echo "Install progressbar -- progressbar function"
pip install -U progressbar
echo "Installing argparse -- argument parser"
pip install -U argparse
echo "Installing pudb -- on screen interactive debugging"
pip install -U pudb
echo "Installing rootpy -- pyRoot done right"
pip install -e $fwk_location/external/src/rootpy

popd