import sys
import time
import parse_bytearray
import numpy as np

BlockSize = 256  # in bytes, important to be the same as in the VHDL code otherwise data could be different


class AcquireAndSaveSingle(object):
    def __init__(self, device, fpgaSwitches, npix, fnum, fignore, ii, sdir, sname):
        # Assumes the opal kelly is flashed, reset and PLL reprogrammed, and FSM activated from previous function.

        print('asdf')
        device.SetWireInValue(0x00, int(fpgaSwitches, 2))
        device.UpdateWireIns()

        # Initialize data
        img = np.zeros(npix, dtype=np.uint64)
        scatt = np.zeros(fnum * npix, dtype=np.uint8)
        goodframes = 0

        device.UpdateWireOuts()
        MemoryCount = device.GetWireOutValue(0x26)
        data_out = bytearray((fnum + fignore) * 1024)  # Bytes
        TransferSize = len(data_out)
        print('     Now transferring {} KB of data from FPGA to PC'.format(TransferSize))
        # print('status 1')

        while MemoryCount < TransferSize:  # /8
            device.UpdateWireOuts()
            # MemoryCount = device.GetWireOutValue(0x26)
            # print('status 2: memory count = %f' % MemoryCount)

        # if MemoryCount >= TransferSize:  # /8
        code = device.ReadFromBlockPipeOut(0xa0, BlockSize, data_out)
        # print('status 3: memory count = %f' % MemoryCount)
        self.timestamp = time.time()

        if code == TransferSize:
            # #save readout data into bytearray
            print('     TransferSize match. Data Retrieved: %.1f kB(frames)' % float(int(code)/1024))
            # with open(args.outputfile + '_img_' + str(i), 'wb') as f:
            #     f.write(data_out)
            #     # print('status 4')
            # with open(args.outputfile + '_timestamp', 'wb') as f:
            #     f.write(timestamp)

            with open(sdir + '\\' + sname + '_unparsed_' + str(ii), 'wb') as f:
                f.write(data_out)
        else:
            print(
                '     TransferSize doesnt match. Amount of data retrieved from Pipe Out is %d Bytes' % code)
            print('     Do not write file!')
            sys.stderr.write(
                "     Data was not retrieved correctly. Error code returned is %d Bytes" % code)
            # print('status 5')

            # reset RAM
            # print('     Current memory count is: %d ' % MemoryCount)
            device.SetWireInValue(0x00, int(0x00000007))
            device.UpdateWireIns()
            device.SetWireInValue(0x00, int(fpgaSwitches, 2))
            device.UpdateWireIns()

            device.UpdateWireOuts()
            MemoryCount = device.GetWireOutValue(0x26)
            # print('status 6')

        self.returnTimestamp()

    def returnTimestamp(self):
        return self.timestamp
