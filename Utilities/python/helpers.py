import os

def syscheck(cmd):
   out = os.system(cmd)
   if out == 0:
      return 0
   else:
      raise RuntimeError("command %s failed executing" % cmd)
