#! /bin/env python

import ROOT
ROOT.gROOT.SetBatch(True)
import rootpy.plotting as plotting
import rootpy
import rootpy.io as io
from URAnalysis.Utilities.roottools import ArgSet, ArgList
from pdb import set_trace
import logging
from os.path import join
import URAnalysis.Utilities.prettyjson as prettyjson
from argparse import ArgumentParser
import uuid
from URAnalysis.Utilities.struct import Struct

asrootpy = rootpy.asrootpy
rootpy.log["/"].setLevel(rootpy.log.ERROR)
rootpy.log["/rootpy"].setLevel(rootpy.log.ERROR)
log = rootpy.log["/harvest_ctag"]
log.setLevel(rootpy.log.ERROR)
ROOT.gStyle.SetOptTitle(0)
ROOT.gStyle.SetOptStat(0)

parser = ArgumentParser()
parser.add_argument('output_file')
parser.add_argument('fitresults', nargs='+')
args = parser.parse_args()

itoy = 0
with io.root_open(args.output_file, 'recreate') as output:
   is_prefit_done = False
   for result in args.fitresults:
      with io.root_open(result) as results:
         if not is_prefit_done:
            is_prefit_done = True
            pref = [i for i in results.GetListOfKeys() if 'prefit' in i.GetName().lower()]
            for key in pref:
               obj = key.ReadObj()
               output.WriteObject(
                  obj,
                  key.GetName()
                  )

         dirs = [i.GetName() for i in results.GetListOfKeys() if i.GetName().startswith('toy_')]
         for dirname in dirs:
            input_dir = results.Get(dirname)
            tdir = output.mkdir('toy_%i' % itoy)
            itoy += 1
            tdir.cd()
            for key in input_dir.GetListOfKeys():
               log.info('saving %s/%s, from %s:%s' % (tdir.GetName(), key.GetName(), result, dirname))
               obj = key.ReadObj()
               tdir.WriteObject(
                  obj,
                  key.GetName()
                  )

