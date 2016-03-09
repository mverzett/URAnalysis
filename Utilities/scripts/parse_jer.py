#! /bin/env python

import argparse
import os
from rootpy.io import root_open 
from rootpy.plotting import F1, Hist1D
from pdb import set_trace

parser = argparse.ArgumentParser()
parser.add_argument('resolution', help='resolution file')
parser.add_argument('sf' , help='sf file')
parser.add_argument('out', help='output root file name')
args = parser.parse_args() 
import ROOT

#
# Parse resolution
# 
header = None
lines = []
with open(args.resolution) as res:
   for line in res:
      if header is None:
         header = line
      else:
         lines.append(line)

#parse header
tokens = header.strip().strip('{}').split()
if not (''.join(tokens)).startswith('1JetEta1JetPt'):
   raise RuntimeError('So far the JER scaler only works with Pt dependent resolution! To avoid crashing later I will crash now')

fcn = F1(tokens[4], name='resolution')

#parse lines
jpt_mins = []
jpt_maxs = []
pars = set()
for line in lines:
   toks = [float(i) for i in line.strip().split()]
   jpt_mins.append(toks[3])
   jpt_maxs.append(toks[4])
   par = tuple(float(i) for i in toks[5:])
   pars.add(par)

if len(pars) != 1:
   raise RuntimeError('Different bins have different resolution function parameters! I don\'t like that!')

fcn.SetRange(min(jpt_mins), max(jpt_maxs))
pars = list(pars)[0]
for i, par in enumerate(pars):
   fcn.SetParameter(i, par)


#
# Parse SF
#
header = None
lines = []
with open(args.sf) as sf:
   for line in sf:
      if not header:
         header = line
      else:
         lines.append(line)

#parse header
tokens = header.strip().strip('{}').split()
if not (''.join(tokens)).startswith('1JetEta0'):
   raise RuntimeError('So far the JER scaler only works with Eta binned SF! To avoid crashing later I will crash now')

bins=set()
sf = [0.]
sf_up = [0.]
sf_dw = [0.]
for line in lines:
   toks = [float(i) for i in line.strip().split()]
   bins.add(toks[0])
   bins.add(toks[1])
   sf.append(toks[3])
   sf_up.append(toks[5])
   sf_dw.append(toks[4])

bins = list(bins)
bins.sort()
hsfc = Hist1D(bins, name='sf_central')
hsfu = Hist1D(bins, name='sf_up')
hsfd = Hist1D(bins, name='sf_down')

def fill(histo, vals):
   for bin, val in zip(histo, vals):
      bin.value = val

fill(hsfc, sf)
fill(hsfu, sf_up)
fill(hsfd, sf_dw)

with root_open(args.out, 'w') as out:
   fcn.Write()
   hsfc.Write()
   hsfu.Write()
   hsfd.Write()
   
   
