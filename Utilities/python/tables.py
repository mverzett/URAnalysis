import re
from pdb import set_trace

class Table(object):
   def __init__(self, *columns, **kwargs):
      self.alias = []
      self.names = []
      self.formats = []
      for i in columns:
         info = i.split(':')
         if len(info) == 2:
            self.alias.append(info[0])
            self.names.append(info[0])
            self.formats.append(info[1])
         elif len(info) == 3:
            self.alias.append(info[0])
            self.names.append(info[1])
            self.formats.append(info[2])
         else:
            raise ValueError('Not all parameters could be set for %s' % i)
      self.separator = kwargs.get('separator', '-')
      self.lines = []
      self.title = kwargs.get('title', '')
   
   def __repr__(self):
      regex = re.compile('\.\d+f')
      header = ' '.join(regex.sub('s', format) % name for format, name in zip(self.formats, self.names))
      separator = self.separator * len(header)
      title = self.title.center(len(header))
      str_lines = [title, header, separator]
      for line in self.lines:
         str_lines.append(
            ' '.join(
               format % val for format, val in zip(self.formats, line)
               )
            )
      
      return '\n'.join(str_lines)

   def add_line(self, *line):
      self.lines.append(line)

   def new_line(self):
      return LineProxy(self)

class LineProxy(object):
   def __init__(self, table):
      self.table = table #__dict__ = dict((i, None)table)
      self.entries = {}

   def __setattr__(self, name, val):
      "x.__setattr__('name', value) <==> x.name = value"
      if name in set(['table', 'entries']):
         super(LineProxy, self).__setattr__(name, val)
      else:
         self.entries[name] = val

   def __setitem__(self, name, val):
      'x.__setitem__(i, y) <==> x[i]=y'
      self.entries[name] = val

   def __del__(self):
      self.table.add_line(
         *[self.entries[i] for i in self.table.alias]
         )
