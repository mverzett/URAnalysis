#!/usr/bin/env python2
#run this script in the job collection directory to add all output files in the subdirectories
import sys, os, time
from glob import glob
import re
import ROOT

allfiles = os.listdir('.')

jobdirs = [d for d in allfiles if os.path.isdir(d)]
regex = re.compile('exit code: (?P<exitcode>\d+)')

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
  files = [f for f in files if ('%s_out_' % dir) in f]

  #check for errors in job processing
  for stdout in stdouts:
    last_line = open(os.path.join(dir, stdout)).readlines()[-1]
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
    merger = ROOT.TFileMerger()
    outfile = dir + '.root'
    print 'merging into %s' % outfile
    merger.OutputFile(outfile)
    files = [dir + '/' + f for f in files]
    for tfile in files:
      merger.AddFile(tfile, False) #why false? no clue, copied from old fwk                                                                                                    
    if not merger.Merge():
      raise RuntimeError('could not merge files into %s' % outfile)

    ##command = 'hadd ' + dir + '.root ' + ' '.join(files)
    ##print command
    ##os.system(command)
  else:
    raise IOError('You asked to merge %i files, but only %i were found.'
                  ' Something must have gone wrong in the batch jobs.' % (num, len(files)))

