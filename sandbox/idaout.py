# This module is derived from examples contained at the following links:
#
# https://stackoverflow.com/questions/32967702/how-to-import-idautils-outside-ida-pro-using-python
# Outdated: https://www.hex-rays.com/blog/running-scripts-from-the-command-line-with-idascript/
#
# It's meant to ease the process of running IDAPython scripts from the commandline.
#
#  1. Create a new script to be invoked via IDA
#  2. Import this module into your script
#  3. Define a `CustomIdaWriter` class that extends `IdaWriter`
#  4. Override the `process` method in `CustomIdaWriter`
#  5. Add the following snippet to the bottom of your script:
#
#     if __name__ == "__main__":
#         writer = CustomIdaWriter()
#         writer.main(sys.argv)
#
# All `stdout` will be redirected to `idaout.txt` in the same directory as your script.
# You can use the `import_data` and `export_data` convenience methods to import/export
# data into your script via `tmp-to-ida.csv` and `tmp-from-ida.csv`, respectively.

import sys
import idaapi
import idc
import os
import csv

class IdaWriter:

    def process(self):
        # extend this class, override the process function, and call main
        return

    def import_data(self, mapping):
        with open('tmp-to-ida.csv') as csvfile:
            data = list(map(lambda row: {
                # https://stackoverflow.com/questions/12229064
                key: func(row) for key, func in mapping.items()
            }, csv.DictReader(csvfile)))
        return data

    def export_data(self, output, fieldnames):
        with open('tmp-from-ida.csv', 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for datum in output:
                writer.writerow(datum)

    def main(self, args):
        # get original stdout and output file descriptor
        f, orig_stdout = self.stdout_to_file('idaout.txt')

        # debug: show arguments passed to script
        # if idc.ARGV:
        #     for i, arg in enumerate(idc.ARGV):
        #         print "[*] arg[{}]: {}".format(i, arg)

        # call the actual logic
        self.process()

        # restore stdout, close output file
        sys.stdout = orig_stdout
        f.close()

        # exit IDA
        idc.Exit(0)

    def stdout_to_file(self, output_file_name, output_dir=None):
        '''Set stdout to a file descriptor

        param: output_file_name: name of the file where standard output is written.
        param: output_dir: output directory for output file, default to script directory.

        Returns: output file descriptor, original stdout descriptor
        '''
        # obtain this script path and build output path
        if not output_dir:
            output_dir = os.path.dirname(os.path.realpath(__file__))

        output_file_path = os.path.join(output_dir, output_file_name)

        # save original stdout descriptor
        orig_stdout = sys.stdout

        # create output file
        f = file(output_file_path, 'w')

        # set stdout to output file descriptor
        sys.stdout = f

        return f, orig_stdout
