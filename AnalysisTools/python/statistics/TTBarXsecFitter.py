from HiggsAnalysis.CombinedLimit.PhysicsModel import *
import URAnalysis.Utilities.prettyjson as prettyjson
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
          setattr(self, key, t(value))
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
        self.opts.add('yieldsJson', '')

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        with open(self.opts.yieldsJson) as jfile:
            yields_json = prettyjson.loads(jfile.read())
        pois = []
        vars_created = [] #this is just to make sure we don't have name clashes
        categories = self.DC.list_of_bins()
        #group categories according to bin number 
        #form a dict with {base category name : (category name, number of jets)} 
        groups = {}
        regex = re.compile('^(?P<base_category>[A-Za-z0-9]+)_(?P<njets>\d+)Jets$')
        for category in categories:
            m = regex.match(category)
            if not m:
                raise ValueError('Category name %s did not match the regex!' % category)
            base = m.group('base_category')
            njets = int(m.group('njets'))
            if base not in groups:
                groups[base] = []
            groups[base].append(category)

        #loop over the base groups, for each of them build
        #  -- ncategories - 1 POI as contribution ratios
        #  -- 1 POI with the total number of events
        #  -- last ratio is (1 - sum(other ratios)), to avoid getting negative
        #     the last ratio is linked to the jet category w/ the most events
        for base, cats in groups.iteritems():
            for signal in self.DC.signals:                
                #make global SF, our REAL POI
                global_sf = '%s_FullYield_%s' % (base, signal)
                total_yield = sum(yields_json[i][signal] for i in cats)
                self.modelBuilder.doVar('%s[%f,0,%f]' % (global_sf, total_yield, total_yield*4)) #range between 0 and 4 times the total yield
                pois.append(global_sf)
                vars_created.append(global_sf)
                
                #sort categories according to the yields of this signal
                yields_by_category = [(i, yields_json[i][signal]) for i in cats]
                yields_by_category.sort(key=lambda x: x[1])
                #make categories ratios (all but last)
                ratio_names = []
                for full_category, category_yield in yields_by_category[:-1]:
                    cat_ratio = '%sYieldRatio_%s' % (full_category, signal)
                    start_val = category_yield/total_yield
                    self.modelBuilder.doVar('%s[%.3f,0,1]' % (cat_ratio, start_val))
                    pois.append(cat_ratio)
                    ratio_names.append(cat_ratio)
                    vars_created.append(cat_ratio)
                #make last ratio, does not create a POI
                full_category, _ = yields_by_category[-1]
                cat_ratio = '%sYieldRatio_%s' % (full_category, signal)
                self.modelBuilder.factory_(
                    'expr::{NAME}("1-{IDXS}", {RATIO_NAMES})'.format(
                        NAME=cat_ratio,
                        IDXS='-'.join(['@%i' % i for i in range(len(ratio_names))]),
                        RATIO_NAMES=','.join(ratio_names)
                        )
                    )
                vars_created.append(cat_ratio)
                
                for full_category, _ in yields_by_category:
                    cat_sf = '%sYield_%s' % (full_category, signal)
                    cat_ratio = '%sYieldRatio_%s' % (full_category, signal)
                    self.modelBuilder.factory_(
                        'expr::{NAME}("@0*@1", {GLOBAL}, {CATEGORY})'.format(
                            NAME=cat_sf,
                            CATEGORY=cat_ratio,
                            GLOBAL=global_sf
                            )
                        )
                    vars_created.append(cat_sf)
        assert(len(vars_created) == len(set(vars_created)))
        self.modelBuilder.doSet('POI',','.join(pois))
                
    def getYieldScale(self,bin,process):
        return '%sYield_%s' % (bin, process) if self.DC.isSignal[process] else 1 

ttxsecfitterWJetCategories = TTBarXsecFittterWithJetsCategories()
