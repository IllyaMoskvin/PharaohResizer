from idashared import IdaInterfacer

import subprocess
import os

class IdaCaller(IdaInterfacer):

    def __init__(self):
        self.input_file = 'tmp-from-ida'
        self.output_file = 'tmp-to-ida'

    def clean_tmp_files(self):
        for file in [self.input_file, self.output_file]:
            if os.path.isfile(file):
                os.remove(file)

    def get_abs_paths(self, script, file):
        # file should already be abs, but not script
        script = os.path.abspath(script)
        file = os.path.abspath(file)

        return script, file

    def run_ida(self, script, file):
        # https://www.hex-rays.com/products/ida/support/idadoc/417.shtml
        subprocess.check_output(['idaq.exe', '-S"' + script + '"', file])

    def call(self, script, file, data, fieldnames, mapping=None):
        script, file = self.get_abs_paths(script, file)

        self.clean_tmp_files()
        self.export_data(data, fieldnames)
        self.run_ida(script, file)

        # if you omit the mapping, we assume you don't want the output
        if os.path.isfile(file) and mapping != None:
            return self.import_data(mapping)
        else:
            return []

    def call_with_list(self, script, file, data, func):
        script, file = self.get_abs_paths(script, file)

        self.clean_tmp_files()
        self.export_data_list(data)
        self.run_ida(script, file)

        if os.path.isfile(file) and func != None:
            return self.import_data_list(func)
