# This module is derived from examples contained at the following links:
#
# https://stackoverflow.com/questions/32967702/how-to-import-idautils-outside-ida-pro-using-python
# Outdated: https://www.hex-rays.com/blog/running-scripts-from-the-command-line-with-idascript/
#
# It's meant to be used when you want to run IDAPython scripts from the commandline,
# rather than from IDA. The main purpose of this class is to provide a way for you
# to see the output of your `print` statements. All `stdout` will be writted to a
# filenamed `idaout.txt` in the same directory as the invoking script. Broadly,
# this script provides a framework for building IDA scripts. You can extend the
# `IdaWriter` class, put your custom logic into the `process` method, and invoke
# the writer by adding something like the following at the bottom of your script:
#
# if __name__ == "__main__":
#     writer = CustomIdaWriter()
#     writer.main(sys.argv)
#
# That said, most of the time, you'll want to output info using e.g. CSV files.

import sys
import idaapi
import idc
import os

class IdaWriter:

    def process(self):
        # extend this class, override the process function, and call main
        return

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
