from rootpy.plotting.views import _MultiFolderView
from URAnalysis.Utilities.roottools import Envelope
from pdb import set_trace

class EnvelopeView(_MultiFolderView):
   def __init__(self, *directories, **kwargs):
      self.kwargs = kwargs
      super(EnvelopeView, self).__init__(*directories) 

   def merge_views(self, objects):
      ret = Envelope()
      for i in objects:
         ret += i
      return ret
