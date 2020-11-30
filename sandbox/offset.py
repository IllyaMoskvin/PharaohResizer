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
#     b. Validates that `cmp` bytes match IDA
#     c. Ensures the address list contains complete instructions

import sys
import subprocess
import operator
import itertools
import os
import csv
from idain import IdaCaller

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

# transform each line into a dictionary, parse values into numbers
diffs = list(map(lambda line: (lambda args = line.split(): {
    # cmp returns the byte number, not the byte offset, e.g.
    # for difference at the first byte, it returns 1, not 0
    'offset': int(args[0], 10) - 1,
    'old': int(args[1], 8),
    'new': int(args[2], 8),
})(), diffs))

caller = IdaCaller()

# map file offsets in `cmp` results to virtual addresses
offset_addresses = caller.call(
    script = 'ida_get_addresses.py',
    file = idb_old,
    fieldnames = ['offset'],
    data = diffs,
    mapping = {
        'offset': lambda row: int(row['offset']),
        'address': lambda row: int(row['address']),
    }
)

# sanity check: throw exception if bytes returned by `cmp` don't match IDA
for target in [(idb_old, 'old'), (idb_new, 'new')]:
    caller.call(
        script = 'ida_validate.py',
        file = target[0],
        fieldnames = ['address', 'byte'],
        data = list(map(lambda oa: {
            'address': oa['address'],
            'byte': filter(lambda diff: diff['offset'] == oa['offset'], diffs)[0][target[1]]
        }, offset_addresses))
    )

# extract just the addresses, this is now our canonical list
addresses = [oa['address'] for oa in offset_addresses]

# we can't break out of nested loops, so put the loops inside a function and return
def extend_addresses(addresses):
    # fill out the address list so that it contains complete instructions
    # alternate doing so between the new and old file until the list stabilizes
    while True:
        for target in [idb_old, idb_new]:
            prev_addresses = list(addresses)
            addresses = caller.call_with_list(
                script = 'ida_extend.py',
                file = target,
                data = addresses,
                func = lambda row: int(row)
            )

            if prev_addresses == addresses:
                return addresses;

# run the address extender on our address list
addresses = extend_addresses(addresses)

# transform address list back into dict
addresses = [{'address': address} for address in addresses]

# get bytes in hex and disasm for full instruction at each address, for both files
def get_instructions(idb_file):
    return caller.call(
        script = 'ida_get_instructions.py',
        file = idb_file,
        fieldnames = ['address'],
        data = addresses,
        mapping = {
            'address': lambda row: int(row['address']),
            'offset': lambda row: int(row['offset']),
            'disasm': lambda row: row['disasm'],
            'bytes': lambda row: row['bytes'],
            'start': lambda row: int(row['start']),
        }
    )

old_instructions = get_instructions(idb_old)
new_instructions = get_instructions(idb_new)

instructions = []

for index, old_instruction in enumerate(old_instructions):
    new_instruction = new_instructions[index]

    if new_instruction['offset'] != old_instruction['offset']:
        raise Exception('misaligned offsets')

    if new_instruction['address'] != old_instruction['address']:
        raise Exception('misaligned addresses')

    instructions.append({
        'address': old_instruction['address'],
        'offset': old_instruction['offset'],
        'old_disasm': old_instruction['disasm'],
        'new_disasm': new_instruction['disasm'],
        'old_bytes': old_instruction['bytes'],
        'new_bytes': new_instruction['bytes'],
        'old_start': old_instruction['start'],
        'new_start': new_instruction['start'],
    })

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

#TODO: format(int(args[1], 8), '02X'),
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
