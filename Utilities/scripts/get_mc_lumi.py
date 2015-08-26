#! /bin/env python

import URAnalysis.Utilities.prettyjson as prettyjson
from argparse import ArgumentParser
import os
import sys
from pdb import set_trace
import logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

__doc__ = 'computes the equivalent luminosity of an MC sample'

parser = ArgumentParser(description=__doc__)
parser.add_argument('metaJson', type=str,
                    help='json file containing the '
                    'meta-information for the sample')
parser.add_argument('samples', type=str,
                    help='json file containing the '
                    'samples definitions')
args = parser.parse_args()

sample_name = os.path.basename(args.metaJson).split('.')[0]
meta_info = prettyjson.loads(open(args.metaJson).read())
samples = prettyjson.loads(open(args.samples).read())

xsection = -1
for sample in samples:
   if sample['name'] == sample_name:
      xsection = sample['xsection']
      break

if xsection == -1:
   logging.warning("Sample %s not found!" % sample_name)

print meta_info['weightedEvents']/float(xsection)


