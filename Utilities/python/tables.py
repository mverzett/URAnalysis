import re
from pdb import set_trace

class Table(object):
   def __init__(self, *columns, **kwargs):
      self.alias = []
      self.names = []
      self.formats = []
      for i in columns:
         info = i.split(':')
         if len(info) == 1:
            self.alias.append(info[0])
            self.names.append(info[0])
            self.formats.append('%s')            
         elif len(info) == 2:
            self.alias.append(info[0])
            self.names.append(info[0])
            self.formats.append(info[1])
         elif len(info) == 3:
            self.alias.append(info[0])
            self.names.append(info[1])
            self.formats.append(info[2])
         else:
            raise ValueError('Not all parameters could be set for %s' % i)
      self.lines = []
      self.title = kwargs.get('title', '')
      self.show_title = kwargs.get('show_title', True)
      self.show_header = kwargs.get('show_header', True)
      regex = re.compile('\.\d+f')
      headers = self.names if self.show_header else ['-' for _ in self.names]
      self.header = ' '.join(regex.sub('s', format) % name for format, name in zip(self.formats, headers))
      self.separator = kwargs.get('separator', '-')*len(self.header)
   
   def __repr__(self):
      header = self.header
      separator = self.separator
      title = self.title.center(len(header))
      str_lines = []
      if self.show_title:
         str_lines.append(title)
      if self.show_header:
         str_lines.extend([header, separator])
      for line in self.lines:
         if line == self.separator:
            str_lines.append( self.separator )
         else:
            str_lines.append(
               ' '.join(
                  format % val for format, val in zip(self.formats, line)
                  )
               )
      
      return '\n'.join(str_lines)

   def add_line(self, *line):
      self.lines.append(line)

   def add_separator(self):
      self.lines.append(self.separator)

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
