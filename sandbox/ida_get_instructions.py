from idaout import IdaRunner
import idaapi
import idc

class CustomIdaRunner(IdaRunner):

    def process(self):
        data = self.import_data({
            'address': lambda row: int(row['address'])
        })

        for datum in data:
            start = idc.ItemHead(datum['address'])
            end = idc.ItemEnd(datum['address'])

            datum['offset'] = idaapi.get_fileregion_offset(datum['address'])
            datum['disasm'] = idc.GetDisasm(datum['address'])
            datum['bytes'] = self.get_bytes_as_hex(start, end)
            datum['start'] = start

        self.export_data(data, ['address','offset', 'disasm', 'bytes', 'start'])

    def get_bytes_as_hex(self, start, end):
        items = idc.GetManyBytes(start, end-start)
        items = [i.encode('hex') for i in items]
        items = [i.upper() for i in items]
        items = ' '.join(items)

        return items

if __name__ == "__main__":
    writer = CustomIdaRunner()
    writer.main(sys.argv)

