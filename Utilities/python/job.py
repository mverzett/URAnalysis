import os
from URAnalysis.Utilities.struct import Struct

class Crab2Cfg(object):
   '''
   Like the cfg infrastructure for crab3, but for crab2
   '''
   def __init__(self, *sections):
      for s in sections:
         self.section(s)

   def section(self, name):
      setattr(self, name, Struct())

   def __repr__(self):
      ret = []
      for section, opts in self.__dict__.iteritems(): #self.sections_.iteritems():
         ret.append('[%s]' % section)
         for opt_name, opt_val in opts.__dict__.iteritems():
            if opt_name.startswith('__') or callable(opt_val): 
               continue
            ret.append("%s = %s" % (opt_name, opt_val))
         ret.append("")
      return '\n'.join(ret)

class Job(object):
   '''
   generalization of a CMSSW job to be submitted 
   with CRAB/batch
   '''
   def __init__(self, pycfg, jobid, simple_name, dbs_name,
                pycfg_args, njobs, lumimask=''):
      self.pycfg = pycfg
      self.name = simple_name 
      self.dbs_name    = dbs_name   
      self.njobs       = njobs      
      self.id       = jobid      
      self.args  = pycfg_args  
      self.mask = lumimask

   def save_as_crab(self):
      from WMCore.Configuration import Configuration
      
      isData = self.name.startswith('data')
      if not isData:
          self.args+=" isMC=True"
      config = Configuration()
      config.section_("General")
      config.General.requestName = '%s_%s' % (self.id, self.name)
      config.section_("JobType")
      config.JobType.psetName = self.pycfg
      config.JobType.pluginName = 'Analysis'
      config.JobType.pyCfgParams = self.args.split()
      config.section_("Data")
      config.Data.inputDataset = self.dbs_name
      config.Data.splitting = 'LumiBased' if isData else 'FileBased'
      config.Data.unitsPerJob = 5
      config.Data.totalUnits = self.njobs
      if self.mask:
         config.Data.lumimask = self.mask
      config.Data.outLFNDirBase = os.path.join(
         '/store/user/', 
         os.environ['USER'],
         self.id,
         self.name
         )
      config.section_("Site")
      config.Site.storageSite = os.environ['URA_STORAGE_SITE']

      crab_cfg_name = 'crab_%s_%s_cfg.py' % (self.id, self.name)
      with open(crab_cfg_name, 'w') as cfg:
         cfg.write(config.pythonise_())

      return crab_cfg_name

   def save_as_crab2(self):
      isData = self.name.startswith('data')
      if not isData:
          self.args+=" isMC=True"
      cfg = Crab2Cfg('CMSSW', 'USER', 'CRAB', 'GRID')
      if isData:
         cfg.CMSSW.total_number_of_lumis=-1
      else:
         cfg.CMSSW.total_number_of_events=-1
      cfg.CMSSW.pset = self.pycfg
      cfg.CMSSW.datasetpath = self.dbs_name
      cfg.CMSSW.pycfg_params = self.args
      cfg.CMSSW.number_of_jobs = self.njobs
      if self.mask:
         config.CMSSW.lumi_mask = self.mask
      
      cfg.USER.return_data = 0
      cfg.USER.publish_data = 0
      cfg.USER.copy_data = 1
      cfg.USER.storage_element = os.environ['URA_CRAB2_SE']
      cfg.USER.storage_path = os.environ['URA_CRAB2_SEPATH']
      cfg.USER.user_remote_dir = os.path.join('/', self.id, self.name, '')
      cfg.USER.ui_working_dir = '_'.join((self.id, self.name))

      cfg.CRAB.scheduler = 'remoteGlidein'
      cfg.CRAB.jobtype = 'cmssw'
      cfg.CRAB.use_server = 0

      cfg.GRID.group = 'uscms'
      cfg.GRID.retry_count = 8

      crab_cfg_name = 'crab_%s_%s.cfg' % (self.id, self.name)
      with open(crab_cfg_name, 'w') as crab:
         crab.write(cfg.__repr__())

      return crab_cfg_name
