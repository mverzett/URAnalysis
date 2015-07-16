#! /bin/env python
__doc__='simple script to read a son file and dump part of it into a new json file'

import URAnalysis.Utilities.prettyjson as prettyjson
from argparse import ArgumentParser

parser = ArgumentParser(description=__doc__)
parser.add_argument('input', metavar='input.json', type=str,
                    help='input json')
parser.add_argument('output', metavar='output.json', type=str,
                    help='Json output file name')
parser.add_argument('toget', metavar='this:that', type=str,
                    help='column-separated list of things to get, means json[this][that]')
#TODO ' futher syntax may be implemented to support list slicing and regex matching')

args = parser.parse_args()
json = prettyjson.loads(
   open(args.input).read()
   )
chain = args.toget.split(':')
to_get = json
for i in chain:
   to_get = to_get[i]

with open(args.output, 'w') as out:
   out.write(
      prettyjson.dumps(
         to_get
         )
      )

