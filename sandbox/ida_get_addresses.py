from idaout import IdaWriter
import idaapi

class CustomIdaWriter(IdaWriter):

    def process(self):
        data = self.import_data({
            'offset': lambda row: int(row['offset'])
        })

        # convert file offset to virtual address
        # https://tech-zealots.com/malware-analysis/understanding-concepts-of-va-rva-and-offset/
        # https://reverseengineering.stackexchange.com/questions/8219/ida-how-to-transform-va-to-fo
        for datum in data:
            datum['address'] = idaapi.get_fileregion_ea(datum['offset'])

        self.export_data(data, ['offset','address'])

if __name__ == "__main__":
    writer = CustomIdaWriter()
    writer.main(sys.argv)
