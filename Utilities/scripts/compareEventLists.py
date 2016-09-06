#! /usr/bin/env python

"""
This script compares two lists of event IDs and prints the differences.

For each input file independently user can provide an optional scheme
that describes how to read an event ID from a line of the file.  The
line can contain several integer numbers separated by any non-numeric
symbols.  The scheme is composed of indices of run, luminosity section,
and event numbers, in the specified order.  Indices start from zero and
are separated by colons.  E.g. scheme '3:1:0' specifies that the first
column in the file contains even numbers, it is followed by luminosity
section numbers, the third column contains some numbers not related to
event IDs, and finally the forth column includes run numbers.  Any
subsequent columns of numbers are ignored.  By default scheme '0:1:2',
i.e. <run>:<lumi>:<event>, is used.
"""

import sys
import argparse
import re


class ErrorEventIDInvalid(Exception):
    """An exeption to be raised when an invalid event ID is used."""
    pass


class EventID(object):
    """A class to describe event ID."""
    
    def __init__(self, runNumber=None, lumiSectionNumber=None, eventNumber=None):
        """Constructor with a complete initialization."""
        
        if runNumber is not None and lumiSectionNumber is not None and eventNumber is not None:
            self.run = int(runNumber)
            self.lumiSection = int(lumiSectionNumber)
            self.event = int(eventNumber)
        else:
            self.run = None
            self.lumiSection = None
            self.event = None
    
    
    def is_valid(self):
        """Check if the ID has been fully initialized."""
        
        return (self.run is not None and self.lumiSection is not None and self.event is not None)
    
    
    def __cmp__(self, other):
        """Comparison operator to define ordering."""
        
        if not self.is_valid() or not other.is_valid():
            raise ErrorEventIDInvalid()
        
        if self.run < other.run:
            return -1
        elif self.run > other.run:
            return +1
        elif self.lumiSection < other.lumiSection:
            return -1
        elif self.lumiSection > other.lumiSection:
            return +1
        elif self.event < other.event:
            return -1
        elif self.event > other.event:
            return +1
        else:
            return 0
    
    
    def __str__(self):
        """String representation used in printing."""
        
        return '{}:{}:{}'.format(self.run, self.lumiSection, self.event)
    
    
    def __hash__(self):
        """Hash method needed to store objects in a set."""
        
        if self.is_valid():
            return hash((self.run, self.lumiSection, self.event))
        else:
            return 0


class SchemeError(Exception):
    """An exception to be raised when a scheme cannot be parsed."""
    pass


class EventIDScheme:
    """Describes how to read an event ID from a line in input file.
    
    Consult description of the module for details.
    """
    
    def __init__(self, scheme):
        """Constructor from a string describing the scheme."""
        
        # A regular expression to parse the scheme
        regex = re.compile(r'^(\d+):(\d+):(\d+)$')
        
        # Match the scheme
        res = regex.search(scheme)
        if res is None:
            raise SchemeError()
        
        # Store positions of each fragment of event ID
        self.runPosition = int(res.group(1))
        self.lumiSectionPosition = int(res.group(2))
        self.eventPosition = int(res.group(3))
        
        # A minimal number of numbers in a string with an event ID
        self.minNumFragments = \
          max(self.runPosition, self.lumiSectionPosition, self.eventPosition) + 1
        
        # A regular expression to define an integer number
        self.intNumberRegEx = re.compile(r'\d+')
    
    
    def ParseLine(self, line):
        """Extract an event ID from the given line.
        
        Return a non-valid event ID if the given line cannot be parsed.
        """
        
        # Find all numbers in the line
        numbers = self.intNumberRegEx.findall(line)
        
        # Check if there is a sufficient number of columns in the line
        # and return event ID
        if len(numbers) >= self.minNumFragments:
            return EventID(
                numbers[self.runPosition], numbers[self.lumiSectionPosition],
                numbers[self.eventPosition]
            )
        else:
            return EventID()


def ParseEventList(fileName, scheme):
    """Read a list of event IDs from a file."""
    
    # Open the source file
    try:
        inputFile = open(fileName, 'r')
    except IOError:
        print 'Error: File "{}" cannot be opened.'.format(fileName)
        sys.exit(1)
    
    
    # Read event IDs from the file
    ids = set()
    
    for line in inputFile.readlines():
        
        # Strip off comments.  If the line includes a comment, this will
        # also remove the terminating new-line symbol, but this is not a
        # problem.
        line = line.split('#')[0]
        
        event = scheme.ParseLine(line)
        if event.is_valid():
            ids.add(event)
    
    if len(ids) == 0:
        print 'Warning: No valid event ID has been found in file "{}".'.format(fileName)
    
    
    inputFile.close()
    return ids


if __name__ == '__main__':
    
    # Define supported arguments and options
    optionParser = argparse.ArgumentParser(description=__doc__)
    optionParser.add_argument(
        'input1', help='First file with event IDs'
    )
    optionParser.add_argument(
        '--scheme1', help='Scheme of storing event ID in first input file',
        default='0:1:2'
    )
    optionParser.add_argument(
        'input2', help='Second file with event IDs'
    )
    optionParser.add_argument(
        '--scheme2', help='Scheme of storing an event ID in second input file',
        default='0:1:2'
    )
    optionParser.add_argument(
        '--labels', help='coma-separated list of labels',
        default='1,2'
    )

    # Parse the arguments and options
    args = optionParser.parse_args()
    f1label, f2label = tuple(args.labels.split(',')) 

    # Read event lists from the input files
    try:
        eventsFile1 = ParseEventList(args.input1, EventIDScheme(args.scheme1))
    except SchemeError:
        print 'Error: Do not understand scheme "{}".'.format(args.scheme1)

    try:
        eventsFile2 = ParseEventList(args.input2, EventIDScheme(args.scheme2))
    except SchemeError:
        print 'Error: Do not understand scheme "{}".'.format(args.scheme2)


    # Find differences between the two sets of events
    diff1 = eventsFile1 - eventsFile2
    diff2 = eventsFile2 - eventsFile1
    print 'Summary:'
    print '  # events in file {}: {}'.format(f1label, len(eventsFile1))
    print '  # events in file {}: {}'.format(f2label, len(eventsFile2))
    print '  # overlap: {}'.format(len(eventsFile1) - len(diff1))
    print '  # in {} but not in {}: {}'.format(f1label, f2label, len(diff1))
    print '  # in {} but not in {}: {}'.format(f2label, f1label, len(diff2))
    print 'Event IDs in file {} but not in file {}:'.format(f1label, f2label)
    diff = diff1

    if len(diff) > 0:
        for event in diff:
            print '', event
    else:
        print ' (none)'
    print ''

    print 'Event IDs in file {} but not in file {}:'.format(f2label, f1label)
    diff = diff2

    if len(diff) > 0:
        for event in diff:
            print '', event
    else:
        print ' (none)'
    print ''
