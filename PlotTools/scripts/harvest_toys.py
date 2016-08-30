#! /bin/env python
from rootpy.io import root_open
from argparse import ArgumentParser
from pdb import set_trace

parser = ArgumentParser()
parser.add_argument('card')
parser.add_argument('shapes')
parser.add_argument('toys')
parser.add_argument('out')
args = parser.parse_args()

procs = []
with open(args.card) as card:
   for line in card:
      if line.startswith('bin') and not procs:
         procs = line.split()[1:]
         break

outtf = root_open(args.out, 'w')
dir_map = dict((i, outtf.mkdir(i)) for i in procs)
shapes = root_open(args.shapes)
templates = dict((i, shapes.Get('%s/data_obs' % i)) for i in procs)

toys_tf = root_open(args.toys)
toys = [i.name for i in toys_tf.toys.keys()]
for toy in toys:
   toyset = toys_tf.toys.Get(toy)

   current_templates = {}
   for i, j in templates.iteritems():
      new = j.Clone()
      new.Reset()
      current_templates[i] = new

   for entry in toyset:
      binno = int(entry.leaves['CMS_th1x'].value+0.5)
      category = procs[entry.leaves['CMS_channel'].index]
      ww = entry.weight
      if ww < 10**-5: continue
      current_templates[category][binno].value = entry.weight
   
   for i, j in current_templates.iteritems():
      dir_map[i].WriteTObject(j, toy)
outtf.Close()
