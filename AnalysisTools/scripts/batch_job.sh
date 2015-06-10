#!/bin/bash
WORKINGDIR=$PWD
cd /uscms_data/d3/verzetti/CMSSW_7_1_5/src/URTTbar
source environment.sh
cd $WORKINGDIR

PA=$@
PA=${PA#* }

EXE=$1

pwd
ls -lht

echo $EXE
echo $PA

$EXE $PA 

exitcode=$? 
echo "exit code: "$exitcode
exit $exitcode 
