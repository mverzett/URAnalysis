from HiggsAnalysis.CombinedLimit.PhysicsModel import *
from pdb import set_trace

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

