#! /bin/env python

import os
from glob import glob
import subprocess
from argparse import ArgumentParser

parser = ArgumentParser(description='wraps crab commands and executes them on mutiple tasks, still needs all the cfgs to me made separately by something else (like our outmated cfg generation)')
tasks = {'submit', 'status', 'kill'}
parser.add_argument('task', type=str, help='what to do. Supported: %s' % (','.join(tasks)))
parser.add_argument('jobid', type=str, help='job id of the production')

args = parser.parse_args()
crab3 = '/cvmfs/cms.cern.ch/crab3/crab-env-bootstrap.sh'

cwd = os.getcwd()
#set the wd as the jobid one
os.chdir(os.path.join(cwd, args.jobid))

if args.task == 'submit':
   cfgs = glob('*.py')
   #check that they are crab cfg
   cfgs = filter(
      lambda x: open(x).readline().startswith('from WMCore.Configuration import Configuration'),
      cfg
      )
   for cfg in cfgs:
      os.system('%s submit -c %s' % (crab3, cfg))
elif args.task == 'status':
   taskdirs = [os.path.dirname(i) for i in glob('*/crab.log')]
   print "Jobs status"
   for task in taskdirs:
      proc = subprocess.Popen(
         [crab3, 'status', task], 
         stdout=subprocess.PIPE, 
         stderr=subprocess.PIPE
         )
      exit_code = proc.wait()
      if exit_code == 0:
         out, _ = proc.communicate()
         lines = out.split('\n')
         #extract the info we care about
         lines = lines[lines.index('')+1:]
         lines = lines[:lines.index('')]
         #make it look nice
         lines = [i.replace('Jobs status:','').replace('\t','') for i in lines]
         print '\t%s:\t %s' % (task, ', '.join(lines))
      else:
         print '\t%s:\t -- status polling failed --'
elif args.task == 'kill':
   taskdirs = [os.path.dirname(i) for i in glob('*/crab.log')]
   for tdir in taskdirs:
      os.system('%s kill %s' % (crab3, tdir))
else:
   raise ValueError('Task option %s is not supported!' % args.task)

#revert to old wd
os.chdir(cwd)

