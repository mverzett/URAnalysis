#! /bin/env python

'''
Simple scripts that open a files and checks validity, than modifies the input file list accordingly
'''

import ROOT
import logging
import sys
log = logging.getLogger("compute_meta")
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
from argparse import ArgumentParser
from progressbar import ProgressBar
from pdb import set_trace


parser = ArgumentParser(description=__doc__)
parser.add_argument(
   'fileLists', nargs='+', type=str,
   help='.txt files containing the location of'
   ' root files to be processed'
   )
args = parser.parse_args()

for lst in args.fileLists:
   infiles = []
   with open(lst) as txt:
      infiles = [i for i in txt]
   made_bad = 0
   made_good = 0
   corrupted = []
   bar = ProgressBar(maxval=len(infiles)).start()
   for idx, line in enumerate(infiles):
      bar.update(idx)
      isbad = line.startswith('#BAD# ')
      fname = line.strip() if not isbad else line.strip().split('#BAD# ')[1]
      fname = fname.replace('root://cmseos.fnal.gov//', '/eos/uscms/')

      tfile = ROOT.TFile(fname)
      ttree = tfile.Get('metaTree/meta') if tfile else None
      try:
         nevts = ttree.GetEntries() if ttree else None
      except:
         nevts = None
      if isbad and not nevts: pass #was bad and still is
      elif not isbad and nevts: pass #was good and still is  
      elif isbad and nevts:
         made_good += 1
         #line = '%s\n' % fname
      elif not isbad and not nevts:
         made_bad += 1
         corrupted.append(fname)
         #line = '#BAD# %s\n' % fname
      if tfile: 
         tfile.Close()
   bar.finish()
   print '%s corrupted:' % lst
   print '\n'.join(corrupted)

   ## if made_bad == 0 and made_good == 0:
   ##    log.info('%s unchanged' % lst)
   ## else:
   ##    log.info('%s --> +%d -%d files' % (lst, made_good, made_bad))
   ##    with open(lst, 'w') as out:
   ##       out.write(''.join(infiles))
print 'DONE!'
