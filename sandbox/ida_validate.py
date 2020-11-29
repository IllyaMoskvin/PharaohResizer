from idaout import IdaRunner
import idc

class CustomIdaRunner(IdaRunner):

    def process(self):
        data = self.import_data({
            'address': lambda row: int(row['address']),
            'cmp_byte': lambda row: int(row['byte']),
        })

        # validate that all the byte values match up
        for datum in data:
            datum['ida_byte'] = idc.Byte(datum['address'])
            if not datum['cmp_byte'] == datum['ida_byte']:
                raise Exception('bytes do not match at offset ' + str(datum['offset'])
                    + ' address ' + format(datum['address'], '08X') + ': '
                    + str(datum['cmp_byte']) + ' vs ' + str(datum['ida_byte']))

if __name__ == "__main__":
    writer = CustomIdaRunner()
    writer.main(sys.argv)
