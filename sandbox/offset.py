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
#     old: 'A1 18 2A 5D 00' # mov     eax, dword_5D2A18
#     new: 'E8 20 6F 16 00' # call    sub_56E570
#
# ...and so on. It does the following:
#
#  1. Uses `cmp` to get the following:
#     a. Get offsets of differences
#     b. Get bytes that are different
#  2. Uses IDAPython to process the differences:
#     a. Maps file offsets to virtual addresses

import sys
import subprocess
import operator
import itertools
import os
import csv

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

# compare the two files using cmp (GNU diffutils) 3.7
try:
    # https://www.freebsd.org/cgi/man.cgi?query=cmp
    cmp_result = subprocess.check_output(['cmp', '-l', sys.argv[1], sys.argv[2]])
except subprocess.CalledProcessError, e:
    if e.returncode != 1: # ok if files differ
        raise
    cmp_result = e.output

# transform result into an array of lines (strings)
diffs = cmp_result.splitlines()

# exit if there's nothing to do
if len(diffs) < 1:
    print >> sys.stderr, "files are identical"
    exit(1)

diffs = list(map(lambda line: (lambda args = line.split(): {
    'old': format(int(args[1], 8), '02X'),
    'new': format(int(args[2], 8), '02X'),
    # cmp returns the byte number, not the byte offset, e.g.
    # for difference at the first byte, it returns 1, not 0
    'offset': int(args[0], 10) - 1,
})(), diffs))

# convenience function for calling ida with a script and passing data around
def call_ida(script, file, fieldnames, data, mapping):
    # clear output from previous script calls
    for csvfile in ['tmp-to-ida.csv', 'tmp-from-ida.csv']:
        if os.path.isfile(csvfile):
            os.remove(csvfile)

    # file should already be abs, but not script
    script = os.path.abspath(script)
    file = os.path.abspath(file)

    # borrowed from `export_data` in `idaout`
    with open('tmp-to-ida.csv', 'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for datum in data:
            writer.writerow(datum)

    # https://www.hex-rays.com/products/ida/support/idadoc/417.shtml
    subprocess.check_output(['idaq.exe', '-S"' + script + '"', file])

    # borrowed from `import_data` in `idaout`
    if os.path.isfile(file):
        with open('tmp-from-ida.csv') as csvfile:
            output = list(map(lambda row: {
                # https://stackoverflow.com/questions/12229064
                key: func(row) for key, func in mapping.items()
            }, csv.DictReader(csvfile)))
    else:
        output = []

    return output

# map file offsets in `cmp` results to virtual addresses
addresses = call_ida(
    script = 'ida_get_addresses.py',
    file = idb_old,
    fieldnames = ['offset'],
    data = diffs,
    mapping = {
        'offset': lambda row: int(row['offset']),
        'address': lambda row: int(row['address']),
    }
)

# everything below is dead code that's being reworked
exit(0)

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
