#! /bin/env python

import URAnalysis.Utilities.prettyjson as prettyjson
from argparse import ArgumentParser
import shutil
import os

parser = ArgumentParser(description=__doc__)
parser.add_argument('output', type=str)
parser.add_argument('inputs', type=str, nargs='+')
args = parser.parse_args()

if len(args.inputs) == 1:
   shutil.copy(args.inputs[0], args.output)
else:
   nevts = 0
   nweighted = 0
   partial = args.output.replace('.json', '.part.json')
   tmp = args.output.replace('.json', '.tmp.json')
   tmp2= args.output.replace('.json', '.tmp2.json')
   with open(partial, 'w') as p:
      p.write(prettyjson.dumps({}))

   for jin in args.inputs:
      jmap = prettyjson.loads(open(jin).read())
      nevts += jmap['events']
      nweighted += jmap['weightedEvents']
      with open(tmp, 'w') as t:
         t.write(prettyjson.dumps(jmap['lumimap']))
      os.system('mergeJSON.py %s %s > %s' % (tmp, partial, tmp2))
      os.system('mv %s %s' % (tmp2, partial))
   
   out = {
      'events' : nevts,
      'weightedEvents' : nweighted,
      'lumimap' : prettyjson.loads(open(partial).read())
      }
   with open(args.output, 'w') as o:
      o.write(prettyjson.dumps(out))      
   os.system("rm %s %s %s" % (tmp, partial, tmp2))
