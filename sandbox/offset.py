#!/usr/bin/env python

# This script converts the output of `cmp`, which looks like this:
#
#   30283 241 350
#   30284  30  40
#   30285  52 157
#   30286 135  26
#
# ...into a YAML file that looks like this:
#
#   - offset: '0000764B'
#     old: 'A1 18 2A 5D'
#     new: 'E8 20 6F 16'
#
# ...and so on.

import sys
import subprocess
import operator
import itertools
import os.path

if len(sys.argv) != 3:
    print >> sys.stderr, "Usage: ./offset.py Old.exe New.exe > offsets.yml"
    exit(1)

file_old = os.path.abspath(sys.argv[1])
file_new = os.path.abspath(sys.argv[2])

# you must manually launch IDAPro (32bit) and load the files to generate idb files
idb_old = file_old[:len(file_old)-4] + '.idb'
idb_new = file_new[:len(file_new)-4] + '.idb'

# make sure that the `exe` and `idb` files exist
for file in [file_old, file_new, idb_old, idb_new]:
    if not os.path.isfile(file):
        print >> sys.stderr, file + " not found"
        exit(1)

try:
    # https://www.freebsd.org/cgi/man.cgi?query=cmp
    # for some reason, cmp returns offsets at +1 relative to every other tool tested
    cmp_result = subprocess.check_output(['cmp', '-i', '1', '-l', sys.argv[1], sys.argv[2]])
except subprocess.CalledProcessError, e:
    if e.returncode != 1: # ok if files differ
        raise
    cmp_result = e.output

diffs = cmp_result.splitlines()

diffs = list(map(lambda line: (lambda args = line.split(): {
    'offset': int(args[0], 10),
    'old': format(int(args[1], 8), '02X'),
    'new': format(int(args[2], 8), '02X'),
})(), diffs))

# https://stackoverflow.com/questions/2154249/identify-groups-of-continuous-numbers-in-a-list
# https://github.com/more-itertools/more-itertools/blob/4d2e1db/more_itertools/more.py#L2384-L2429
def consecutive_groups(iterable, ordering=lambda x: x):
    for k, g in itertools.groupby(
        enumerate(iterable), key=lambda x: x[0] - ordering(x[1])
    ):
        yield map(operator.itemgetter(1), g)

chunks = [n for n in consecutive_groups(diffs, lambda diff: diff['offset'])]

chunks = list(map(lambda diffs: {
    # https://stackoverflow.com/questions/51053227
    'offset': format(diffs[0]['offset'], '08X'),
    'old': ' '.join(map(operator.itemgetter('old'), diffs)),
    'new': ' '.join(map(operator.itemgetter('new'), diffs)),
}, chunks))

print '---';

for chunk in chunks:
    print "- offset: '%s'" % chunk['offset']
    print "  old: '%s'" % chunk['old']
    print "  new: '%s'" % chunk['new']
    print
