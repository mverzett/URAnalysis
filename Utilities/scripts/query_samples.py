#! /bin/env python

import URAnalysis.Utilities.prettyjson as prettyjson
from pprint import pprint
import argparse
import os
from fnmatch import fnmatch

parser = argparse.ArgumentParser()
parser.add_argument('query', help='posix regex query')

args = parser.parse_args()

samples_path = os.path.join(os.environ['URA_PROJECT'], 'samples.json')
if not os.path.isfile(samples_path):
   raise RuntimeError('%s not found' % samples_path)

samples = prettyjson.loads(
   open(samples_path).read()
   )

for sample in samples:
   if fnmatch(sample['name'], args.query):
      pprint(sample)
