#! /bin/env python

'''
Takes as input a root file name and the path for the TTree
to use as sample. Builds in place a C++ code to read it
named URStreamer.C
'''

import os, sys
from argparse import ArgumentParser
from pdb import set_trace
import URAnalysis.AnalysisTools.autocode.types as cpp_types
parser = ArgumentParser(__doc__)
parser.add_argument('tfile_name', type=str)
parser.add_argument('tree_path', type=str)
parser.add_argument('--nodict', action='store_false')
parser.add_argument('--projectdir', type=str, help='project location where to copy files', default='.')

args = parser.parse_args()

import ROOT
tfile = ROOT.TFile.Open(args.tfile_name)
if not tfile:
   raise ValueError('%s does not exist!' % args.tfile_name)

tree  = tfile.Get(args.tree_path)
if not tree:
   raise ValueError('%s does not exist!' % args.tree_path)

branches = [cpp_types.BranchMeta(i) for i in tree.GetListOfBranches()]
objects  = set(i.name.split(cpp_types._separator)[0] for i in branches if i.is_object)
objects  = [cpp_types.ObjectMeta(
      i, 
      [j for j in branches if j.name.startswith(i)]
      ) for i in objects]

streamer = cpp_types.StreamerMeta(branches, objects)

with open('URStreamer.h', 'w') as output:
   output.write(streamer.cpp_dump())

if args.nodict:
   ## NOT NEEDED AS THE CODE IS IN C++
   ldef = cpp_types.LinkDefMeta(objects)
   with open('LinkDef.h', 'w') as output:
      output.write(ldef.cpp_dump())

   #Compile macro
   #ROOT.gROOT.ProcessLine('.L URStreamer.C+')
   os.system('rootcint -f Dict.cxx -c ./URStreamer.h LinkDef.h')
   os.system('g++ -Wall -shared -fPIC -o Dict.so Dict.cxx `root-config --cflags --glibs`')


#copy files
project_dir = args.projectdir
os.system('mv URStreamer.h %s/interface/.' % project_dir)
if args.nodict:
   os.system('mv Dict.h %s/interface/.' % project_dir)
   os.system('mv Dict.so %s/lib/.' % project_dir)
   os.system('rm LinkDef.h')
   os.system('rm Dict.cxx')

