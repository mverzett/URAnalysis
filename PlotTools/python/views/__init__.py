#Make it look like a package
from glob import glob
from os import environ
from os.path import basename

#gather all the files here
modules = [basename(i.replace('.py','')) for i in glob('%s/PlotTools/python/views/[A-Z]*.py' % environ['URA'])]
__all__ = []
for module in modules:
    __import__(module, globals(), locals(), [module])
    __all__.append(module)


