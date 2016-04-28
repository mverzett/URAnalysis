from HiggsAnalysis.CombinedLimit.PhysicsModel import *
import URAnalysis.Utilities.prettyjson as prettyjson
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
          default = getattr(self, key)
          if isinstance(default, bool):
              setattr(self, key, t(eval(value)))
          else:
              setattr(self, key, t(value))
       else:
          raise ValueError(
             "Model option %s not recognised!"
             " Available options are: %s" %(key, ','.join(self.opts))
             )
       

class CTagEfficiency(PhysicsModel):
    def __init__(self):
        PhysicsModel.__init__(self)
        self.opts = PhysOpts()
        self.opts.add('fitLightEff', True)
        self.opts.add('verbose', False)
        self.opts.add('inclusive', False)
        self.opts.add('POIPropagation', True)
        self.opts.add('lightConstantsJson', '')
        self.paganini = True #avoid repetitions
        self.exprs = {}
        self.pars  = ['signal_norm', 'LCharmE', 'SLightE', 'lead_cfrac', 'LLightE', 'SCharmE', 'sub_cfrac']
        self.categories = set(['notag', 'leadtag', 'subtag', 'ditag'])
        self.constants = None

    def setPhysicsOptions(self,physOptions):
        '''Receive a list of strings with the physics options from command line'''
        for po in physOptions:
           self.opts.parse(po)
        if self.opts.inclusive:
            self.categories = set(['Inc_nolead', 'Inc_nosub', 'Inc_leadtag', 'Inc_subtag'])
        if self.opts.lightConstantsJson:
            self.constants = prettyjson.loads(open(self.opts.lightConstantsJson, 'r').read())
            if not self.opts.fitLightEff:
                self.pars.remove('SLightE')
                self.pars.remove('LLightE')
                self.pars.extend(['mc_lead_light_eff', 'mc_sub_light_eff', self.constants['light_SF']['nuisance_name']])
            

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        #tt signal strenght 0-200% on over-all right combination ttbar scaling
        #self.modelBuilder.doVar('strength[4347,0,8000]') 
        #what we actually want to measure
        self.modelBuilder.doVar('charmSF[1,0.,2.]')
        if self.opts.fitLightEff:
            print 'PASSING HERE', self.opts.fitLightEff
            self.modelBuilder.doVar('lightSF[1,0.,2.]')
            self.modelBuilder.doSet('POI','charmSF,lightSF')
        else:
            self.modelBuilder.doSet('POI','charmSF')

        self.exprs = {
            'notag'   : 'expr::Scaling_notag(  "signal_norm*((1-LCharmE)*(1-SLightE)*lead_cfrac+(1-LLightE)*(1-SCharmE)*sub_cfrac+(1-LLightE)*(1-SLightE)*(1-lead_cfrac-sub_cfrac))", {PARS})',
            'leadtag' : 'expr::Scaling_leadtag("signal_norm*(LCharmE*(1-SLightE)*lead_cfrac+LLightE*(1-SCharmE)*sub_cfrac+LLightE*(1-SLightE)*(1-lead_cfrac-sub_cfrac))", {PARS})',
            'subtag'  : 'expr::Scaling_subtag( "signal_norm*((1-LCharmE)*SLightE*lead_cfrac+(1-LLightE)*SCharmE*sub_cfrac+(1-LLightE)*SLightE*(1-lead_cfrac-sub_cfrac))", {PARS})',
            'ditag'   : 'expr::Scaling_ditag(  "signal_norm*(LCharmE*SLightE*lead_cfrac+LLightE*SCharmE*sub_cfrac+LLightE*SLightE*(1-lead_cfrac-sub_cfrac))", {PARS})',
            ############################
            ##  INCLUSIVE CATEGORIES  ##
            ############################
            'Inc_nolead'  : 'expr::Scaling_Inc_nolead( "signal_norm*((1-LCharmE)*lead_cfrac+(1-LLightE)*(1-lead_cfrac))", {PARS})',
            'Inc_nosub'   : 'expr::Scaling_Inc_nosub(  "signal_norm*((1-SCharmE)*sub_cfrac+(1-SLightE)*(1-sub_cfrac))", {PARS})',
            'Inc_leadtag' : 'expr::Scaling_Inc_leadtag("signal_norm*(LCharmE*lead_cfrac+LLightE*(1-lead_cfrac))", {PARS})',
            'Inc_subtag'  : 'expr::Scaling_Inc_subtag( "signal_norm*(SCharmE*sub_cfrac+SLightE*(1-sub_cfrac))", {PARS})',
            }

    @staticmethod
    def replace_pars(expr, pars):
        idx = 0
        out_pars = []
        for par in pars:
            if par in expr:
                expr = expr.replace(par, '@%i' % idx)
                out_pars.append(par)
                idx += 1
        return expr, out_pars

    def getYieldScale(self,bin,process):
        #check category (bin) consistency
        if bin not in self.categories:
            raise ValueError(
                'Asking information for bin %s, but allowed bins are %s, '
                'did you forget the inclusive=True option?' % (bin, self.categories))

        if self.paganini:
            #make products of MC efficiency * SF to make category yields less painful
            #L(eading)/S(ubleading) Charm/Light E(fficiency)
            self.modelBuilder.factory_('expr::LCharmE("@0*@1", charmSF, mc_lead_charm_eff)')
            self.modelBuilder.factory_('expr::SCharmE("@0*@1", charmSF, mc_sub_charm_eff )')
            if self.opts.fitLightEff:
                self.modelBuilder.factory_('expr::LLightE("@0*@1", lightSF, mc_lead_light_eff)') 
                self.modelBuilder.factory_('expr::SLightE("@0*@1", lightSF, mc_sub_light_eff )') 

        if self.DC.isSignal[process]:
            expr = self.exprs[bin]
            if not self.opts.fitLightEff:
                if not self.constants:
                    raise RuntimeError("Running without light SF Fit requires having the constants json!")
                constant = self.constants['light_SF'][bin]
                adder = '+' if constant >= 0 else ''
                lsf = '(1{adder}{cnst}*{nuis})'.format(adder=adder, cnst=constant, nuis=self.constants['light_SF']['nuisance_name']) #light scale factor
                print bin, process, constant, lsf
                expr = expr.replace('LLightE', 'mc_lead_light_eff*%s' % lsf).replace('SLightE', 'mc_sub_light_eff*%s' % lsf)
            expr, pars = CTagEfficiency.replace_pars(expr, self.pars)
            expr = expr.format(PARS=(', '.join(pars)))
            try:
                self.modelBuilder.factory_(expr)
            except RuntimeError as e:
                if str(e) == 'Error in factory statement':
                    raise RuntimeError('%s: %s' % (str(e), expr))
                else:
                    raise e
            return 'Scaling_%s' % bin
        elif self.opts.POIPropagation:
            #print 'POI propagation'
            #Set POI yield effect on non-signals
            varname = '%s_%s_charmScale' % (bin, process)
            expr = 'expr::%s("%s", charmSF)' % (varname, self.constants['charm_SF'][bin][process])
            self.modelBuilder.factory_(expr)
            if self.opts.fitLightEff:
                lvname = '%s_%s_lightScale' % (bin, process)
                expr = 'expr::%s("%s", lightSF)' % (lvname, self.constants['light_SF'][bin][process])
                self.modelBuilder.factory_(expr)
                gname = '%s_%s_globalScale' % (bin, process)
                self.modelBuilder.factory_('expr::%s("@0*@1", %s, %s)' % (gname, lvname, varname))
                varname = gname
            return varname
        else:
            return 1.
        ## if self.paganini:
        ##     if self.opts.verbose:
        ##         self.modelBuilder.out.Print()
        ##     self.paganini = False



ctagEfficiency = CTagEfficiency()


class CTagComplete(PhysicsModel):
    def __init__(self):
        PhysicsModel.__init__(self)
        self.opts = PhysOpts()
        self.opts.add('verbose', False)
        self.opts.add('constants', '')
        self.effs_done = set()
        self.categories = {
            'notag'   : (False, False),
            'leadtag' : (True , False),
            'subtag'  : (False, True ),
            'ditag'   : (True , True ),
            }
        self.constants = None

    def setPhysicsOptions(self,physOptions):
        '''Receive a list of strings with the physics options from command line'''
        for po in physOptions:
           self.opts.parse(po)
        self.constants = prettyjson.loads(open(self.opts.constants).read())

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        #tt signal strenght 0-200% on over-all right combination ttbar scaling
        #self.modelBuilder.doVar('strength[4347,0,8000]') 
        #what we actually want to measure
        self.modelBuilder.doVar('charmSF[1,0.,2.]')
        self.modelBuilder.doVar('lightSF[1,0.,2.]')
        self.modelBuilder.doVar('beautySF[1,0.,2.]')
        self.modelBuilder.doSet('POI','charmSF,lightSF,beautySF')

    @staticmethod
    def replace_pars(expr, pars):
        idx = 0
        out_pars = []
        for par in pars:
            if par in expr:
                expr = expr.replace(par, '@%i' % idx)
                out_pars.append(par)
                idx += 1
        return expr, out_pars

    def getYieldScale(self,bin,process):
        name = 'Scaling_%s_%s' % (bin, process)
        if self.modelBuilder.out.function(name):
            return name
        #check category (bin) consistency
        if bin not in self.categories:
            raise ValueError(
                'Asking information for bin %s, but allowed bins are %s, '
                'did you forget the inclusive=True option?' % (bin, self.categories))

        ltag, stag = self.categories[bin]
        ntot = self.constants[process]['normalization']

        leff = 'L%sE'+ ('_%s' % process)
        seff = 'S%sE'+ ('_%s' % process)
        
        l_template = '%s' if ltag else '(1-%s)' 
        s_template = '%s' if stag else '(1-%s)' 
        factor_template = 'expr::{FACTOR}("{MCEFF}*@0", {FLAV}SF)'

        flavours = []
        num_flav = 0 #for debug
        pars = set()
        for mapping in self.constants[process]['flavours']:
            lead, sub, weight = tuple(mapping)
            if weight > 0.:
                partial = weight #for debug
                eff_var = leff % lead
                pars.add(eff_var)
                l_factor = l_template % eff_var
                eff = self.constants['mceffs'][lead]["leading"][process] #for debug
                partial *= eff if ltag else (1-eff) #for debug
                if eff_var not in self.effs_done:
                    cmd = factor_template.format(
                        FACTOR=eff_var,
                        MCEFF=self.constants['mceffs'][lead]["leading"][process],
                        FLAV=lead
                        )
                    self.modelBuilder.factory_(cmd)
                    self.effs_done.add(eff_var)
                eff_var = seff % sub
                pars.add(eff_var)
                s_factor = s_template % eff_var
                eff = self.constants['mceffs'][sub]["subleading"][process] #for debug
                partial *= eff if stag else (1-eff) #for debug
                num_flav += partial  #for debug 
                if eff_var not in self.effs_done:
                    cmd = factor_template.format(
                        FACTOR=eff_var,
                        MCEFF=self.constants['mceffs'][sub]["subleading"][process],
                        FLAV=sub
                        )
                    self.modelBuilder.factory_(cmd)
                    self.effs_done.add(eff_var)
                ww = str(weight)
                pair_factor = '*'.join([l_factor, s_factor, ww])
                flavours.append( pair_factor )
        formula = 'expr::%s("%f*(%s)", {PARS})' % (name, ntot, ' + '.join(flavours))
        #print '%s/%s' % (bin, process), formula
        formula, pars = CTagComplete.replace_pars(formula, pars)
        formula = formula.format(PARS=(', '.join(pars)))
        self.modelBuilder.factory_(formula)
        print '%s/%s' % (bin, process), ntot*num_flav#, '-->', self.modelBuilder.out.function(name).getVal()
        return name


effcomplete = CTagComplete()
