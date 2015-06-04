from rootpy.io import DoesNotExist
from pdb import set_trace

class MultifileView(object):
   def __init__(self, **names_and_files):
      self.__dict__ = names_and_files

   def Get(self, path):
      psplit = path.split('/')
      root_dir = psplit[0]
      following = '/'.join(psplit[1:])
      ret = None
      if root_dir not in self.__dict__:
         if '' in self.__dict__:
            try:
               ret = self.__dict__[''].Get(path)
            except DoesNotExist as e:
               ret = None
         else:
            ret = None
      else:
         ret = self.__dict__[root_dir].Get(following)

      if ret == None:
         raise DoesNotExist('could not find %s in %s' % (path, self.__class__.__name__))
      return ret
