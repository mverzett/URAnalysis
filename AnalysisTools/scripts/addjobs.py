#!/usr/bin/env python2
#run this script in the job collection directory to add all output files in the subdirectories
import sys, os, time
from glob import glob
import re
import ROOT
from pdb import set_trace
from Queue import Queue
from subprocess import Popen, PIPE
import time
from fnmatch import fnmatch
from argparse import ArgumentParser

parser = ArgumentParser(__doc__)
parser.add_argument(
   '--fastHadd', action='store_true',
   help='Use DQM fastHadd instead of normal hadd. Gain speed, but works only on histograms'
   )

args = parser.parse_args()

allfiles = os.listdir('.')

jobdirs = [d for d in allfiles if os.path.isdir(d)]
regex = re.compile('exit code: (?P<exitcode>\d+)')
tasks_queue = Queue()

for dir in jobdirs:
  print dir
  if dir + '.root' in allfiles:
    continue
  confile = open(dir+'/condor.jdl', 'r')
  info = confile.read().split('\n')
  confile.close()
  info = [l.strip() for l in info if 'Queue' in l]
  num =  int(info[0].split('Queue')[1].strip())
  files = os.listdir(dir)
  stdouts = [i for i in files if '.stdout' in i]
  pattern = '%s_out_*.%s' % (dir, 'dat' if args.fastHadd else 'root')
  files = [f for f in files if fnmatch(f, pattern)]

  #check for errors in job processing
  for stdout in stdouts:
    try:
      last_line = open(os.path.join(dir, stdout)).readlines()[-1]
    except:
      raise RuntimeError('Problem reading %s' % stdout)
    match = regex.match(last_line)
    if match:
      exitcode = int(match.group('exitcode'))
      if exitcode != 0 :
        raise IOError('Condor job %s in %s did not complete properly and exited'
                      ' returing status %i' % (stdout, os.path.join(os.getcwd(),dir), exitcode))
    else:
      raise ValueError("cannot match %s with exit code regex!" % last_line)

  print num, len(files)
  if num == len(files):
    outfile = dir + '.root'
    print 'merging into %s' % outfile
    files = [dir + '/' + f for f in files]
    if args.fastHadd:
      if len(files) > 1:
        cmd = ['fastHadd', 'add', '-j', '6', '-o', '%s.dat' % dir]
        cmd.extend(files)
        os.system(' '.join(cmd))
      else:
        os.system('cp %s %s.dat' % (files[0], dir))
      cmd = ['fastHadd', 'convert', '-o', '%s.root' % dir, '%s.dat' % dir]
      os.system(' '.join(cmd))
    else:
      tasks_queue.put((outfile, files))
  else:
    raise IOError('You asked to merge %i files, but only %i were found.'
                  ' Something must have gone wrong in the batch jobs.' % (num, len(files)))

if args.fastHadd: sys.exit(0)
print "starting parallel merging..."
tasks = []
task_map = {}
while not tasks_queue.empty():
  running = [t for t in tasks if t.poll() is None]
  done = [t for t in tasks if t.poll() is not None]
  #check hadd success
  if not all(i.returncode == 0 for i in done):
    set_trace()
    for t in done:
      if t.returncode != 0:
        out, err = t.communicate()
        cmd = task_map[t]        
        print 'Failed merging %s with error' % cmd[3]
        print err
        os.system('rm %s' % cmd[3])
    raise RuntimeError('Some files failed to merge!')
  if len(running) < 5:
    out, infiles = tasks_queue.get()
    cmd = ['hadd', '-O', '-f', out] + infiles
    print ' '.join(cmd)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    task_map[proc] = cmd
    running.append(
      proc
      )
  tasks = running
  time.sleep(10)

for t in tasks:
  ret = t.wait()
  if ret != 0:
    out, err = t.communicate()
    cmd = task_map[t]        
    print 'Failed merging %s with error' % cmd[3]
    print err
    os.system('rm %s' % cmd[3])
    raise RuntimeError('Some files failed to merge!')

  
        


