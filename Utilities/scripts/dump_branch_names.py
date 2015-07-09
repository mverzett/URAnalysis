#! /usr/bin/env python
'''
Like edmDumpEventContent, but for custom trees.
The --type option prints together with the branch
name also the C++ type for the branch
'''

import sys
if len(sys.argv) < 3 or '-h' in sys.argv or '--help' in sys.argv:
    print 'Usage dump_branch_names.py file.root path/to/Tree (--type, -t)'
    print __doc__
    sys.exit(1)

print_type = '--type' in sys.argv or '-t' in sys.argv
#Open sample file
import ROOT
from pdb import set_trace
ROOT.gROOT.SetBatch(True)
tfile = ROOT.TFile.Open(sys.argv[-2])

tree = tfile.Get(sys.argv[-1])
#Get All the branches
if print_type:
    names = []
    types = []
    for branch in tree.GetListOfBranches():
        names.append(branch.GetName())
        if hasattr(branch, 'GetTypeName'):
            types.append(branch.GetTypeName())
        elif branch.GetClassName():
            types.append(branch.GetClassName())
        else:
            types.append(branch.GetListOfLeaves().At(0).GetTypeName())
    max_name = max(names, key=len)
    max_type = max(types, key=len)
    format = '%'+str(len(max_type))+'s   %'+str(len(max_name))+'s'
    print '\n'.join([format % i for i in zip(types, names)])
else:
    print '\n'.join([branch.GetName() for branch in tree.GetListOfBranches()])
tfile.Close()
