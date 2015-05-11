from rootpy.io import DoesNotExist

class MultifileView(object):
   def __init__(self, *names_and_files):
      self.__dict__ = dict(names_and_files)

   def Get(self, path):
      psplit = path.split('/')
      root_dir = psplit[0]
      following = '/'.join(psplit[1:])
      if root_dir not in self.__dict__:
         raise DoesNotExist('could not find %s in %s' % (path, self.__class__.__name__))
      return self.__dict__[root_dir].Get(following)
