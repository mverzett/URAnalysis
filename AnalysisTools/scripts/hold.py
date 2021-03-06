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
parser.add_argument(
   '--failThr', type=float, help='Failure rate above which something strange is going on and we should not resubmit',
   default=0.2
   )
parser.add_argument(
   '--outtype', help='output extension',
   default='root'
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

regex = re.compile('exit code: (?P<exitcode>\d+)')
stdout_format = 'con_(?P<id>\d+).stdout'
stdout_regex = re.compile(stdout_format)
def check_correct(taskdir, sample, output_extension='root'):
   sample_dir = os.path.join(taskdir, sample)
   #get jdl
   jdl_f = os.path.join(sample_dir, 'condor.jdl')
   njobs =0
   with open(jdl_f) as jdl:
      for line in jdl:
         if line.lower().startswith('queue'):
            nqueued = line.lower().replace('queue','').strip()
            njobs += int(nqueued) if nqueued else 1
   
   #Get stdouts
   stdouts = glob.glob('%s/*.stdout' % sample_dir)
   failed = []
   present = [False for _ in range(njobs)]
   out_present = [False for _ in range(njobs)]
   #check the exit codes
   for log in stdouts:
      logname = os.path.basename(log)
      log_id = int(stdout_regex.match(logname).group('id'))
      present[log_id] = True #bit string would be faster, but who cares?
      out_present[log_id] = os.path.isfile('%s/%s_out_%d.%s' % (sample_dir, sample, log_id, output_extension))
      lines = open(log).readlines()
      last_line = lines[-1] if len(lines) else 'exit code: 999' #fake wrong exit code
      match = regex.search(last_line)
      if match:
         exitcode = int(match.group('exitcode'))
         if exitcode != 0 :
            failed.append(logname)
      else:               
         raise ValueError("cannot match %s with exit code regex! in %s" % (last_line, log))

   #print sample, len(failed), 'jobs with bad exit codes'
   #check if some jobs did not yield stdout at all
   for idn, info in enumerate(present):
      if not info:
         failed.append(
            stdout_format.replace('(?P<id>\d+)', '%d' % idn)
            )

   #print sample, len(failed), 'jobs with bad exit codes or missing stdout'
   #check if some jobs failed producing output
   for idn, info in enumerate(out_present):
      if not info:
         failed.append(
            stdout_format.replace('(?P<id>\d+)', '%d' % idn)
            )
   #print sample, len(failed), 'jobs with bad exit codes or missing out'
   return njobs, failed
   

escape = False
start = time.time()
totjobs = -1
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
         #get samples
         samples = [os.path.basename(i) for i in glob.glob('%s/*' % args.check_correctness) if os.path.isdir(i)]
         njobs = {}
         failed_samples = {}
         #check correctness for each sample
         for sample in samples:
            nj, failed = check_correct(args.check_correctness, sample, args.outtype)
            njobs[sample] = nj
            if failed:
               failed_samples[sample] = failed

         #if everything is right
         if len(failed_samples) == 0:
            print " exiting..."
            escape = True
         else:            
            for sample, lfailed in failed_samples.iteritems():
               ntotal = float(njobs[sample])
               nfailed = len(lfailed)
               ratio = nfailed/ntotal
               if ntotal > 5 and ratio > args.failThr:
                  print "sample %s has %.0f%% of failed jobs, this is suspicious, please check" % (sample, ratio*100)
                  escape = True
            if not escape and submission <= args.maxResubmission:
               submission += 1
               print " %i samples failed to complete properly! Resubmitting them..." % len(failed_samples)
               cwd = os.getcwd()
               for sample, jobs in failed_samples.iteritems():
                  condor_dir = os.path.join(args.check_correctness, sample)
                  os.chdir(condor_dir)
                  print "Sample %s has %d failed jobs, resubmitting them" % (sample, len(jobs))
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
