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

parser = ArgumentParser(description=__doc__)
parser.add_argument('jobid', type=str, help='job id of the production')
parser.add_argument('options', type=str, help='command-line arguments'
                    ' to be passed to the configuration')
parser.add_argument('--njobs', type=int, help='how many jobs should I run?'
                    ' (-1 for one for each input file)', default=1000)
parser.add_argument('--samples', dest='samples', type=str,
                    nargs='+', help='Samples to run on, POSIX regex allowed')
parser.add_argument('--sample-def', dest='sample_def', type=str,
                    help='json file containing the samples definition ')
parser.add_argument('--crab', dest='crab', action='store_true',
                    default=False, help='Submit to crab')
parser.add_argument('--local', dest='local', action='store_true',
                    default=False, help='Submit to local (NOT SUPPORTED YET)')

args = parser.parse_args()

if not os.path.isfile(args.sample_def):
   raise ValueError('file %s does not exist' % args.sample_def)
   
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
      'make_pat_and_ntuples.py',
      args.jobid,
      sample.name,
      sample.DBSName,
      args.options,
      args.njobs,
      sample.__dict__.get('lumimask', '')
      )
   for sample in to_submit
]

if args.crab:
   crab_cfgs = [job.save_as_crab() for job in jobs]
   print 'To submit run:'
   print '\n'.join('crab submit %s' % cfg for cfg in crab_cfgs)
