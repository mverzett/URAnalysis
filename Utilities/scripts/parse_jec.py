#! /bin/env python

import argparse
import os
from rootpy.io import root_open 
from rootpy.tree import Tree
from pdb import set_trace

##parser = argparse.ArgumentParser()
##parser.add_argument('inputdir', help='directory with JECS')
##parser.add_argument('payload' , help='type of jets')
##parser.add_argument('levels'  , nargs='+', help='type of jets')
##parser.add_argument('-o', default='out.root', help='output name')
##
##args = parser.parse_args()
import ROOT

def tokenize(line):
   tokens = line.strip().split()
   tokens = [i.strip() for i in tokens if i.strip()]
   ret = []
   for token in tokens:
      if token.startswith('#'):
         break
      else:
         ret.append(token)
   return ret

with root_open('test.root', 'w') as outfile:
   with open('Summer15_25nsV6_MC_L1FastJet_AK8PFchs.txt') as infile:
      print "opening file"
      corr_tree = Tree('L1')   
      corr_tree.create_branches({
            'min' : 'F',
            'max' : 'F',
            })
      fcn = None
      bin_vars = None
      fcn_vars = None
      n_bin_vars = None
      n_fcn_vars = None
      for line in infile:
         tokens = tokenize(line)
         print "parsing line", line
         if not fcn:
            tokens = [i.strip('{}') for i in tokens]
            n_bin_vars = int(tokens[0])
            bin_vars = tokens[1:n_bin_vars+1]
            n_fcn_vars = int(tokens[n_bin_vars+1])
            fcn_vars = tokens[n_bin_vars+2:n_bin_vars+2+n_fcn_vars]
            formula = tokens[n_bin_vars+2+n_fcn_vars]
            if n_fcn_vars == 1:
               fcn = ROOT.TF1('fcn', formula)
               corr_tree.Branch('fcn', 'TF1', fcn)
            elif n_fcn_vars == 2:
               fcn = ROOT.TF2('fcn', formula)
               corr_tree.Branch('fcn', 'TF2', fcn)
            elif n_fcn_vars == 3:
               fcn = ROOT.TF3('fcn', formula)
               corr_tree.Branch('fcn', 'TF3', fcn)
         else:
            corr_tree.min = float(tokens[0])
            corr_tree.max = float(tokens[1])
            var_ranges = tokens[3:n_fcn_vars*2+3]
            fcn_pars = tokens[n_fcn_vars*2+3:]
            for i, par_value in enumerate(fcn_pars):
               fcn.SetParameter(i, float(par_value))
            ranges = [float(j) for i,j in enumerate(var_ranges) if i % 2 == 0]
            ranges.extend([float(j) for i,j in enumerate(var_ranges) if i % 2 == 1])
            fcn.SetRange(*ranges)
            corr_tree.Fill()
      corr_tree.Write()
      
