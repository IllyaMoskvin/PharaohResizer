from idaout import IdaRunner
import idaapi

class CustomIdaRunner(IdaRunner):

    def process(self):
        data = self.import_data_list(lambda row: int(row))

        output = []

        # fill out the address list so that it contains complete instructions
        for datum in data:

            # extract the start and end address for the instruction at this address
            start = idc.ItemHead(datum);
            end = idc.ItemEnd(datum)

            # if the start is before current address, append any bytes between the start
            # and the current address, which are not (yet) present in the output, nor the
            # input (if that's the case, we'll get to them eventually)
            if (start < datum):
                for address in range(start, datum):
                    if not (address in data or address in output):
                        output.append(address)

            # append the current address
            output.append(datum)

            # same as before, but now between current address and end
            if (datum < end):
                for address in range(datum, end):
                    if not (address in data or address in output):
                        output.append(address)

        # it should already be in order, but sort just in case
        output.sort()

        self.export_data_list(output)

if __name__ == "__main__":
    writer = CustomIdaRunner()
    writer.main(sys.argv)
