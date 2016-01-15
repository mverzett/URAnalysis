#! /bin/env python

from rootpy.io import root_open
from argparse import ArgumentParser
from pdb import set_trace
from fnmatch import fnmatch

parser = ArgumentParser(__doc__)
parser.add_argument('tfile_name', type=str)
parser.add_argument('branch_match', type=str)

args = parser.parse_args()

tfile = root_open(args.tfile_name)
ttree = tfile.Events

branches = [i for i in ttree.branchnames if fnmatch(i, args.branch_match)]
for entry in ttree:
   for branch_name in branches:
      val = getattr(entry, branch_name)
      if hasattr(val, '__len__'):
         val = [i for i in val] #unpack vectors
      print "%s --> %s"% (branch_name, val.__repr__())
   cmd = raw_input('press enter to inspect next entry, type exit to quit: ')
   if cmd.lower() == 'exit':
      break

