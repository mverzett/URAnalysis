#! /bin/env python

from argparse import ArgumentParser
import URAnalysis.Utilities.prettyjson as prettyjson
from URAnalysis.PlotTools.BasePlotter import BasePlotter, LegendDefinition
from pdb import set_trace
from rootpy.plotting import Graph
import os

parser = ArgumentParser()
parser.add_argument('limits', nargs='+', help='file.json:label_to_give')
parser.add_argument('--show', default='exp0', help='what should be shown', choices=['exp0', 'exp+1', 'exp+2', 'exp-1', 'exp-2', 'obs'])
parser.add_argument('--out', default='comparison')
args = parser.parse_args()

colors = ['black', '#4169e1', '#cc2c44', '#008000', '#ff9a00', '#b000ff']
if len(colors) < len(args.limits):
	raise RuntimeError('I have more limits than colors to display them!')

limits = []
for info in args.limits:
	fname, label = tuple(info.split(':'))
	jmap = prettyjson.loads(open(fname).read())
	graph = Graph(len(jmap.keys()))
	points = [(float(p), float(vals[args.show])) for p, vals in jmap.iteritems()]
	points.sort()
	for idx, info in enumerate(points):
		p, val = info
		graph.SetPoint(idx, p, val)
	graph.title = label
	limits.append(graph)
	
outdir = os.path.dirname(args.out)
base = os.path.basename(args.out)
plotter = BasePlotter(outdir)
plotter.overlay(
	limits, legend_def=LegendDefinition(position='NE'), 
	xtitle='mass', ytitle='limit', 
	linecolor=colors,
	linewidth=2,
	drawstyle=['AL']+['L' for _ in colors],
	legendstyle='l',
	)
plotter.save('base')
