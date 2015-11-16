#! /bin/env python

'''
holds the process until all condor jobs are done
'''

import subprocess, time, os, glob, re
from argparse import ArgumentParser
from pdb import set_trace

parser = ArgumentParser(__doc__)
parser.add_argument(
   '--check_correctness', type=str, help='check that every stdout '
   'has exit code 0, marking proper ending. Provide root submission directory', 
   default=''
   )
parser.add_argument(
   '--maxResubmission', type=int, help='resubmit the jobs a maximum of times',
   default=3
   )

args = parser.parse_args()

def rescue(jdl, nrescue, to_rescue):
   proc_lines = []
   header_lines = []
   with open(jdl) as submitter:
      for line in submitter:
         if line.startswith('Queue'):
            continue
         if '$(Process)' in line:
            proc_lines.append(line)
         else:
            header_lines.append(line)

   header_lines.append('\n')
   header_lines.append('\n')
   
   rescuer = os.path.join(
      os.path.dirname(jdl),
      'condor.rescue%i.jdl' % nrescue
      )
   print "rescue %i -- rescuing %i jobs from sample %s" % (nrescue, len(to_rescue), os.path.basename(os.path.dirname(jdl)))
   with open(rescuer, 'w') as rescue:
      rescue.write(''.join(header_lines))
      for ijob in to_rescue:
         proc = [i.replace('$(Process)', str(ijob)) for i in proc_lines]
         proc.extend(['Queue', '\n', '\n'])
         rescue.write(''.join(proc))
   return rescuer

escape = False
start = time.time()
totjobs = -1
regex = re.compile('exit code: (?P<exitcode>\d+)')
submission = 0

while not escape:
   proc = subprocess.Popen(
      ["condor_q", os.environ['USER']], 
      stderr=subprocess.PIPE, stdout=subprocess.PIPE
      )
   stdout, stderr = proc.communicate()
   last = stdout.split('\n')[-2]
   njobs = int(last.split()[0])
   eta = 'UNKNOWN'
   if totjobs <> -1:
      elapsed = time.time() - start
      completed = totjobs - njobs
      if completed != 0:
         eta_time = njobs*(elapsed/completed)
         m, s = divmod(eta_time, 60)
         h, m = divmod(m, 60)
         eta = "%d:%02d:%02d" % (h, m, s)
   else:
      totjobs = njobs
   if njobs == 0:
      print "Jobs completed!",
      if args.check_correctness:
         stdouts = glob.glob(os.path.join(args.check_correctness, '*/*.stdout'))
         failed_samples = {}
         for log in stdouts:
            lines = open(log).readlines()
            last_line = lines[-1] if len(lines) else 'exit code: 999' #fake wrong exit code
            match = regex.search(last_line)
            if match:
               exitcode = int(match.group('exitcode'))
               if exitcode != 0 :
                  key = os.path.dirname(log)
                  if key not in failed_samples:
                     failed_samples[key] = []
                  failed_samples[key].append(os.path.basename(log))
            else:               
               raise ValueError("cannot match %s with exit code regex! in %s" % (last_line, log))
         if len(failed_samples) == 0:
            print " exiting..."
            escape = True
         else:
            if submission <= args.maxResubmission:
               submission += 1
               print " %i samples failed to complete properly! Resubmitting them..." % len(failed_samples)
               cwd = os.getcwd()
               for condor_dir, jobs in failed_samples.iteritems():
                  os.chdir(condor_dir)
                  id_getter = re.compile(r'con_(?P<id>\d+)\.stdout')
                  job_ids = [int(id_getter.match(i).group('id')) for i in jobs]
                  for idjob in job_ids:
                     os.system("rm *_out_{ID}.root con_{ID}.*".format(ID=idjob))
                  rescued = rescue("condor.jdl", submission, job_ids)
                  print "rescuing %s" % os.path.join(condor_dir, rescued)
                  os.system("condor_submit %s" % rescued)
               os.chdir(cwd)
            else:
               print (" There are still some failing samples, bet the maximum numbers"
                      "of resubmission was reached, exiting...")
               escape = True
      else:        
         print " exiting..."
         escape = True
   else:
      print "%i jobs are still running, checking again in 30 seconds. ETA: %s" % (njobs, eta)
      time.sleep( 30 )
