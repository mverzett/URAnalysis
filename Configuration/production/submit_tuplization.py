#! /bin/env python

#
# Submit Tuplization to crab or local
#
#

#monkey-patch the dictionary      

import URAnalysis.Utilities.prettyjson as prettyjson
import sys
from URAnalysis.Utilities.fnselect import fnselect
from URAnalysis.Utilities.job import Job
from URAnalysis.Utilities.struct import Struct
from argparse import ArgumentParser
from pdb import set_trace
import os
import subprocess

parser = ArgumentParser(description=__doc__)
parser.add_argument('jobid', type=str, help='job id of the production')
parser.add_argument('--options', type=str, help='command-line arguments'
                    ' to be passed to the configuration', default="")
parser.add_argument('--njobs', type=int, help='how many jobs should I run?'
                    ' (-1 for one for each input file)', default=1000)
parser.add_argument('--samples', dest='samples', type=str,
                    nargs='+', help='Samples to run on, POSIX regex allowed', default=["*"])
parser.add_argument('--sample-def', dest='sample_def', type=str,
                    help='json file containing the samples definition ', default="%s/samples.json" % os.environ["URA_PROJECT"])
parser.add_argument('--crab', dest='crab', type=int,
                    default=0, help='Version of crab to use')
parser.add_argument('--local', dest='local', action='store_true',
                    default=False, help='Submit to local (NOT SUPPORTED YET)')

args = parser.parse_args()

if not (bool(args.crab) or args.local):
   raise ValueError('You did not specify how you want to run! (crab2/3 or local)')

if args.crab <> 0:
   proc = subprocess.Popen(
      'voms-proxy-info', 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE
      )
   if proc.wait() <> 0:
      print "No grid proxy available, creating one"
      subprocess.call('voms-proxy-init -voms cms')
   proc = subprocess.Popen(
      'voms-proxy-info', 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE
      )
   if proc.wait() <> 0:
      raise RuntimeError('could not create a valid GIRD proxy!')
   stdout, _ = proc.communicate()
   hn_name = stdout.split('\n')[0].split('/CN=')[1]
   os.environ['HN_NAME'] = hn_name   

if not os.path.isfile(args.sample_def):
   raise ValueError('file %s does not exist' % args.sample_def)
   
if not os.path.isdir(args.jobid):
   os.makedirs(args.jobid)

all_samples = [Struct(**i) for i in prettyjson.loads(open(args.sample_def).read())]
to_submit = reduce(
   lambda x,y: x+y, 
   [fnselect(all_samples, pattern, key=lambda x: x.name) for pattern in args.samples],
   []
)
#remove duplicate samples selected by multiple patterns

to_submit = set(to_submit)

jobs = [
   Job(
      '../make_pat_and_ntuples.py',
      args.jobid,
      sample.name,
      sample.DBSName,
      args.options,
      args.njobs,
      os.path.join(os.environ['URA_PROJECT'], sample['lumimask']) if 'lumimask' in sample else '',
      sample.__dict__.get('computeWeighted', True)
      )
   for sample in to_submit
]

if args.crab == 3:
   crab_cfgs = [job.save_as_crab(args.jobid) for job in jobs]
   print 'To submit run:'
   print 'cd %s' % args.jobid
   print '\n'.join('crab3 submit -c %s' % cfg for cfg in crab_cfgs)
elif args.crab == 2:
   crab_cfgs = [job.save_as_crab2(args.jobid) for job in jobs]
   print 'To submit run:'
   print 'cd %s' % args.jobid
   print 'source %s' % os.environ['CRAB2_LOCATION']
   print '\n'.join('crab -create -cfg %s' % cfg for cfg in crab_cfgs)
   print '\n'.join('crab -submit -c %s' % cfg.strip('crab_').split('.')[0] for cfg in crab_cfgs)
