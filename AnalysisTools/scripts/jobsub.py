#!/usr/bin/env python2
import sys, os, time
from pdb import set_trace
from glob import glob
from argparse import ArgumentParser
import re
import URAnalysis.Utilities.prettyjson as prettyjson
from URAnalysis.PlotTools.data_views import get_best_style, log #not for the same purpose, but the same mechanism
#import rootpy
log.setLevel(log.CRITICAL)

swdir = os.path.realpath(os.environ['URA_PROJECT'])
jobid = os.environ['jobid']
inputdir = os.path.join(swdir, 'inputs')
inputdir = os.path.join(inputdir, jobid)

parser = ArgumentParser('submit analyzer to the batch queues')
parser.add_argument('jobdir')
parser.add_argument('executable')
parser.add_argument('--opts', default='', help='options to be passed to the analyzer')
parser.add_argument('--samples', nargs='*', help='samples to be analyze (full regex supported')
parser.add_argument('--splitting', default='10', help='splitting to be used, either an integer of a valid path')
parser.add_argument('--nocfg', action='store_true', help='do not provide job cfg')
parser.add_argument('--notransfer', action='store_true', help='do not provide additional input files')
parser.add_argument('--nosubmit', action='store_true', help='does not submit the jobs')
parser.add_argument('--noconversion', action='store_true', help='does not convert into .dat format')

args = parser.parse_args()

jobdir = args.jobdir
exe = args.executable
jobargs = args.opts
filters = [re.compile(i) for i in args.samples] \
   if args.samples else [re.compile('.*')]

#os.mkdir('Production_'+ time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime()))
if os.path.isdir(jobdir):
	print jobdir, 'exists: EXIT'
	sys.exit(-1)
os.mkdir(jobdir)

samplefiles = glob(os.path.join(inputdir, '*.txt'))

#the cfg of the executable we want to run
exe_cfg = os.path.join(
        swdir,
        '%s.cfg' % exe
)

#external inputs: SFs, JEC and so forth
externals = glob(
        os.path.join(swdir, 'inputs', 'data', '*.*')
)

#external inputs, jobid specific: PU reweighting, TTSolver training (prob.root), ecc
externals_jobid_specific = glob(
        os.path.join(swdir, 'inputs', jobid, 'INPUT', '*.*')
)
transferfiles = [exe_cfg]+externals+externals_jobid_specific

transferfiles_config = ', '.join(transferfiles)

filesperjob = 10
splitting = None
if os.path.isfile(args.splitting):
  splitting = prettyjson.loads(open(args.splitting).read())
else:
        filesperjob = int(args.splitting)

for sf in samplefiles:
  infile = os.path.join(inputdir, sf)
  sample = os.path.basename(sf).split('.txt')[0]
  if splitting:
    filesperjob = get_best_style(sample, splitting)
  if not any(i.match(sample) for i in filters): continue
  jobpath = os.path.join(
          jobdir, 
          sample
          )
  os.mkdir(jobpath)
  infiledes = open(infile, 'r')
  numrootfiles = infiledes.read().count('.root')
  infiledes.close()
  numjobs = max(numrootfiles/filesperjob, 1)
  numjobs = numjobs if numrootfiles > numjobs else numrootfiles
  print "submitting sample %s in %d jobs, ~1 every %d" % (sample, numjobs, filesperjob)

  transfer = 'Transfer_Input_Files = %s' % transferfiles_config if not args.notransfer else ''
  condorfile ="""universe = vanilla
Executable = batch_job.sh
Should_Transfer_Files = YES
WhenToTransferOutput = ON_EXIT
{transfer_statement}
Output = con_$(Process).stdout
Error = con_$(Process).stderr
Log = con_$(Process).log
request_memory = 5000
Arguments = {exe} {input} {sample}_out_$(Process).root {cfg} --thread 1 --j $(Process) --J {njobs} {options}
Queue {njobs}

	""".format(
          transfer_statement=transfer,
          exe=exe, 
          input=infile, 
          sample=sample,
          cfg='-c %s' % os.path.basename(exe_cfg) if not args.nocfg else '',
          njobs=numjobs, 
          options=jobargs
          )
  
  conf = open(os.path.join(jobpath, 'condor.jdl'), 'w')
  conf.write(condorfile)
  conf.close()

  conversion='''
#EXPERIMENTAL!
toutfile=`for i in $PA; do echo $i; done | grep '\.root'`
outname="${toutfile%.*}"
echo fastHadd encode -o $outname.dat $toutfile
fastHadd encode -o $outname.dat $toutfile
'''
  batch_job="""#!/bin/bash
WORKINGDIR=$PWD
cd {0}
source environment.sh
cd $WORKINGDIR

PA=$@
PA=${{PA#* }}

EXE=$1

pwd
ls -lht

echo $EXE
echo $PA

$EXE $PA 

exitcode=$? 
{1}
echo "exit code: "$exitcode
exit $exitcode 
	""".format(swdir, conversion if not args.noconversion else '')
  
  conf = open(os.path.join(jobpath, 'batch_job.sh'), 'w')
  conf.write(batch_job)
  conf.close()

  if not args.nosubmit:
          os.system('cd ' + jobpath + ' && condor_submit condor.jdl')

