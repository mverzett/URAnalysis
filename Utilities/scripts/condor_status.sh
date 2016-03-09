#! /bin/env bash

condor_q -wide $USER > .condor.log
last=`tail -n 1 .condor.log`
for infile in $(ls $URA_PROJECT/inputs/$jobid/*.txt); do
    txt=`basename $infile`
    sample="${txt%.*}"
    njobs=`grep -c $sample'\.' .condor.log`
    if [ "$njobs" != "0" ]; then
        echo $sample $njobs
    fi
done
echo $last
rm .condor.log