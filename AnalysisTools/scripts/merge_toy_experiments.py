#! /bin/env python

import ROOT
ROOT.gROOT.SetBatch(True)
import rootpy
import rootpy.io as io
from pdb import set_trace
from argparse import ArgumentParser

asrootpy = rootpy.asrootpy
rootpy.log["/"].setLevel(rootpy.log.ERROR)
rootpy.log["/rootpy"].setLevel(rootpy.log.ERROR)
log = rootpy.log["/merge_toy_experiments"]
log.setLevel(rootpy.log.INFO)

parser = ArgumentParser()
parser.add_argument('output_file')
parser.add_argument('toy_files', nargs='+')
args = parser.parse_args()

itoy = 0
with io.root_open(args.output_file, 'recreate') as output:
   toy_dir = output.mkdir('toys')
   for result in args.toy_files:
      log.info("Merging: %s" % result)
      with io.root_open(result) as toyfile:
         for key in toyfile.toys.keys():
            obj = key.read_obj()
            toy_dir.WriteTObject(obj, 'toy_%i' % itoy)
            itoy += 1
log.info("Successfully merged %i files, for a total of %i toys" % (len(args.toy_files), itoy))
