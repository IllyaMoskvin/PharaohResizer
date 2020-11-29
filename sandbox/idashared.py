import csv

class IdaInterfacer:

    def __init__(self):
        self.input_file = None
        self.output_file = None

    def import_data(self, mapping):
        with open(self.input_file) as csvfile:
            return list(map(lambda row: {
                # https://stackoverflow.com/questions/12229064
                key: func(row) for key, func in mapping.items()
            }, csv.DictReader(csvfile)))

    def export_data(self, output, fieldnames):
        with open(self.output_file, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for datum in output:
                writer.writerow(datum)

    def import_data_list(self, func):
        with open(self.input_file) as file:
            return list(map(func, file.read().splitlines()))

    def export_data_list(self, output):
        with open(self.output_file, 'wb') as file:
            for datum in output:
                file.write("%s\n" % datum)
