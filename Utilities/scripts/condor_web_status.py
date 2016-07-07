#! /bin/env python

import subprocess
import os
from glob import glob
from argparse import ArgumentParser
from pdb import set_trace

parser = ArgumentParser(description=__doc__)
parser.add_argument('jobdir', help='job directory')
parser.add_argument('rootout', action='store_true', help='count root file instead of .dat')
args = parser.parse_args()

def grep_first(fname, pattern):
	with open(fname) as jfile:
		for line in jfile:
			if line.startswith(pattern):
				return line.strip()
	return None

html = '''
<!DOCTYPE html>
<html lang="en-US">
<head>
<title>FNAL Jobreport</title>
<link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css">
</head>
<body>
{0}
</body>
</html>
'''

progbar =	'''<div class="progress"> 
	<div class="progress-bar progress-bar-success" role="progressbar" style="width:{done}%"></div>
	<div class="progress-bar progress-bar-info"    role="progressbar" style="width:{run}%"></div>
	<div class="progress-bar progress-bar-danger"  role="progressbar" style="width:{fail}%"></div>
	</div>'''

table = '<table width="90%">{0}</table>'
tab_row = '''<tr>{0}</tr>'''
txt_cell = '<td width="10%" align="center" valign="middle">{0}</td>'
bar_cell = '<td width="80%" valign="middle">{0}</td>'
pre = '<pre>{0}</pre>'

proc = subprocess.Popen(['condor_q', '-wide', os.environ['USER']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = proc.communicate()
ret = proc.returncode
if ret != 0:
	raise RuntimeError('condor call failed with %s' % err)

lines = out.split('\n')
last = lines[-2]
samples = [os.path.basename(i) for i in glob('%s/inputs/%s/*.txt' % (os.environ['URA_PROJECT'], os.environ['jobid']))]
running = {i : 0 for i in samples}
idle = {i : 0 for i in samples}
print 'scanning condor jobs'
for line in lines:
	for sam in samples:
		if sam in line:
			if '  R  ' in line:
				running[sam] += 1
			else:
				idle[sam] += 1				
			break

success = {}
fail = {}
print 'scanning outputs'
for sample in samples:
	sam = sample.split('.')[0]
	samdir = os.path.join(args.jobdir, sam)
	if not os.path.isdir(samdir):
		continue
	jdl = os.path.join(samdir, 'condor.jdl')
	line = grep_first(jdl, 'Queue')
	njobs = int(line.strip().split()[1])
	
	with open(jdl) as jfile:
		for line in jfile:
			if line.startswith('Queue'):
				njobs = int(line.strip().split()[1])
				break
	file_type = '*.root' if args.rootout else '*.dat'
	files = glob(os.path.join(samdir,file_type))
	success[sample] = 0
	fail[sample] = 0
	for idx in range(njobs):
		stdout = os.path.join(samdir, 'con_%i.stdout' % idx)
		grepped = grep_first(stdout, 'exit code')
		if grepped:
			ecode = int(grepped.split(':')[1].strip())
			if ecode != 0:
				fail[sample] += 1
				continue
			delivered = False
			end = '_%i.%s' % (idx, 'root' if args.rootout else 'dat')
			for fname in files:
				if fname.endswith(end):
					delivered = True
					break
			if delivered:
				success[sample] += 1
			else:
				fail[sample] += 1

infos = []
def percent(part, total):
	return int(float(part)*100/total)

for sample in samples:
	if sample not in success and \
			 sample not in fail and \
			 running[sample] == 0 and \
			 idle[sample] == 0:
		continue
	total = running[sample]+idle[sample]
	ok = 0
	bad = 0
	if sample in success:
		total += success[sample]
		ok = success[sample]
	if sample in fail:
		total += fail[sample]
		bad = fail[sample]
	
	infos.append((
			sample.split('.')[0], percent(ok, total), percent(running[sample], total), percent(bad, total)))

rows = [(name, progbar.format(done=i, run=j, fail=k)) for name, i, j, k in infos] #make bars
rows = [ (txt_cell.format(i), bar_cell.format(j))for i, j in rows] #build cells
rows = [ tab_row.format(''.join(i)) for i in rows] #build rows
tab = table.format('\n'.join(rows)) #build table
plast = pre.format(last)

with open('/uscms/home/%s/public_html/jobs.html' % os.environ['USER'], 'w') as out:
	out.write(html.format('\n'.join([tab, plast])))
