#! /bin/env python

import URAnalysis.Utilities.prettyjson as prettyjson
import URAnalysis.Utilities.das as das
from argparse import ArgumentParser
import shutil
from copy import deepcopy
from fnmatch import fnmatch

parser = ArgumentParser(description=__doc__)
parser.add_argument('json')
parser.add_argument('newProd')
parser.add_argument('--valid', action='store_true', help='require the dataset to be valid, otherwise any status is displayed')
args = parser.parse_args()

shutil.copyfile(args.json, '%s.bak' % args.json)
json = prettyjson.loads(open(args.json).read())

for sample in json:
	das_name = sample['DBSName']
	if sample['name'].startswith('data'):
		print 'This is data! (%s) Skipping..' % das_name
		continue
	elif das_name == "TO BE SET":
		print "The sample %s has no associated DAS entry! Skipping..." % sample['name']
		continue
	elif das_name.startswith('TO BE UPDATED -- '):
		das_name = das_name.replace('TO BE UPDATED -- ', '')
	_, prim_dset, prod, tier = tuple(das_name.split('/'))

	if fnmatch(prod, args.newProd):
		print "%s already matches! Skipping..." % sample['name']
		continue

	query = 'dataset dataset=%s status=%s' % \
		 ('/'.join(['',prim_dset, args.newProd, tier]), 'VALID' if args.valid else '*')
	newsamples = das.query(query, True)
	print 'Availeble options'
	for info in enumerate(newsamples):
		print '[%d] %s' % info
	print '[%d] None of the above' % len(newsamples)
	idx = raw_input('Which should I pick? ')
	while isinstance(idx, str):
		try:
			idx = int(idx)
		except:
			idx = raw_input('%s is not a number! plase repeat: ' % idx)
			
	if idx == len(newsamples):
		print "OK, I'm skipping the sample and putting a 'TO BE UPDATED -- ' before the old sample"
		sample['DBSName'] = 'TO BE UPDATED -- %s' % das_name
	else:
		sample['DBSName'] = str(newsamples[idx])

with open(args.json, 'w') as out:
	out.write(prettyjson.dumps(json))
