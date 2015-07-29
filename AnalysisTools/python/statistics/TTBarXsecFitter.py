from HiggsAnalysis.CombinedLimit.PhysicsModel import *
from pdb import set_trace
import re

class PhysOpts(object):
    def __init__(self):
       self.opts = set()
    def add(self, name, default=0.):
       setattr(self, name, default)
       self.opts.add(name)
    def parse(self, opt):
       key,value =tuple(opt.split('='))
       if key in self.opts:
          t = type(getattr(self, key))
          setattr(self, key, t(eval(value)))
       else:
          raise ValueError(
             "Model option %s not recognised!"
             " Available options are: %s" %(key, ','.join(self.opts))
             )
       

class TTBarXsecFittter(PhysicsModel):
    def __init__(self):
        PhysicsModel.__init__(self)
        self.opts = PhysOpts()
        self.opts.add('verbose', False)
        self.exprs = {}

    def setPhysicsOptions(self,physOptions):
        '''Receive a list of strings with the physics options from command line'''
        for po in physOptions:
           self.opts.parse(po)

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        pois = []
        #float freely each category
        for category in self.DC.list_of_bins():
            for signal in self.DC.signals:
                poi = '%sYieldSF_%s' % (category, signal)
                pois.append(poi)
                self.modelBuilder.doVar('%s[1,0,4]' % poi)
        self.modelBuilder.doSet('POI',','.join(pois))
        #TODO: add inter-variable constraints
        
    def getYieldScale(self,bin,process):
        return '%sYieldSF_%s' % (bin, process) if self.DC.isSignal[process] else 1 


ttxsecfitter = TTBarXsecFittter()

class TTBarXsecFittterWithJetsCategories(TTBarXsecFittter):
    def __init__(self):
        TTBarXsecFittter.__init__(self)
        #super(TTBarXsecFittterWithJetsCategories, self).__init__()
        self.opts.add('startingRatios', '')

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        start_ratios = eval(self.opts.startingRatios) if self.opts.startingRatios else {}
        pois = []
        categories = self.DC.list_of_bins()
        #group categories according to bin number 
        #form a dict with {base category name : (category name, number of jets)} 
        groups = {}
        regex = re.compile('^(?P<base_category>[A-Za-z0-9]+)_Jets(?P<njets>\d+)$')
        for category in categories:
            m = regex.match(category)
            if not m:
                raise ValueError('Category name %s did not match the regex!' % category)
            base = m.group('base_category')
            njets = int(m.group('njets'))
            if base not in groups:
                groups[base] = []
            groups[base].append((category, njets))

        #loop over the base groups, for each of them build
        #  -- ncategories - 1 POI as contribution ratios
        #  -- 1 POI with the total number of events
        #  -- last ratio is (1 - sum(other ratios)), to avoid getting negative
        #     the last ratio is linked to the 0 jets category (w/ the most events)
        for base, cats in groups.iteritems():
            #sort them to #jets
            sorted_cats = sorted(
                cats, 
                key=lambda x: x[1],
                reverse=True
                )

            for signal in self.DC.signals:
                #make global SF, our REAL POI
                global_sf = '%sYieldSF_%s' % (base, signal)
                self.modelBuilder.doVar('%s[1,0,4]' % global_sf)
                pois.append(global_sf)
                
                #make categories ratios (all but last)
                ratio_names = []
                for full_category, njets in sorted_cats[:-1]:
                    cat_ratio = '%sYieldRatio_%s' % (full_category, signal)
                    start_val = start_ratios[full_category] if full_category in start_ratios else 1./len(cats) 
                    self.modelBuilder.doVar('%s[%.3f,0,4]' % (cat_ratio, start_val))
                    pois.append(cat_ratio)
                    ratio_names.append(cat_ratio)
                #make last ratio, does not create a POI
                full_category, njets = sorted_cats[-1]
                cat_ratio = '%sYieldRatio_%s' % (full_category, signal)
                self.modelBuilder.factory_(
                    'expr::{NAME}("1-{IDXS}", {RATIO_NAMES})'.format(
                        NAME=cat_ratio,
                        IDXS='-'.join(['@%i' for i in range(len(ratio_names))]),
                        RATIO_NAMES=','.join(ratio_names)
                        )
                    )
                
                for full_category, njets in sorted_cats:
                    cat_sf = '%sYieldSF_%s' % (full_category, signal)
                    cat_ratio = '%sYieldRatio_%s' % (full_category, signal)
                    self.modelBuilder.factory_(
                        'expr::{NAME}("@0*@1", {GLOBAL}, {CATEGORY})'.format(
                            NAME=cat_sf,
                            CATEGORY=cat_ratio
                            )
                        )
                

ttxsecfitterWJetCategories = TTBarXsecFittterWithJetsCategories()
