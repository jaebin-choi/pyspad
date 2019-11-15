import sys
import time
import ok
import os
import argparse
import parse_bytearray
import numpy as np


class AcqOK(object):
    def __init__(self, flash, reset, reprogpll, parseenable, saveenable, getdata,
                 numpix, bitfile, rstcode, fpgaSwitches, clkdiv, duty, phase, flen, fignore, fnum, inum, sdir, sname):

        fnum = int(fnum)
        fignore = int(fignore)
        numpix = int(numpix)

        # FIND AND OPEN THE OPAL KELLY (CAN ONLY RECOGNIZE SINGLE DEVICE) ----------- ----------- ----------- ----------- -----------
        device = ok.okCFrontPanel()
        device.OpenBySerial(device.GetDeviceListSerial(0))

        # FLASH DEVICE
        if flash == 1:
            flerr = device.ConfigureFPGA(bitfile)
            print('     Flashing device with error code ', flerr)

        if device.IsFrontPanelEnabled():  # IsFrontPanelEnabled returns true if FrontPanel is detected.
            # print("     FrontPanel host interface enabled.")
            pass
        else:
            sys.stderr.write("     FrontPanel host interface not detected.")

        # INITIALIZE FPGA ----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- -----------
        error_list = []
        # RESET EVERYTHING
        if reset == 1:
            # print('     Fully resetting device')
            error_list.append(device.SetWireInValue(0x00, int(rstcode)))
            device.UpdateWireIns()
            time.sleep(0.5)
            # set everything to rest
            device.SetWireInValue(0x00, int(0x00000000))
            device.UpdateWireIns()

        # WIREINS
        # device.SetWireInValue(0x01, int(ep01wire)) #not used
        device.SetWireInValue(0x02, int(flen))
        # device.SetWireInValue(0x03, int(ep03wire))
        device.SetWireInValue(0x04, int(clkdiv))
        device.UpdateWireIns()

        # REPROGRAM PLL
        if reprogpll == 1:
            device.SetWireInValue(0x05, int(phase))
            device.SetWireInValue(0x06, int(duty))
            # device.SetWireInValue(0x07, int(args.clkout1phase))
            # device.SetWireInValue(0x08, int(args.clkout1duty))
            # device.SetWireInValue(0x09, int(args.clkout2phase))
            # device.SetWireInValue(0x10, int(args.clkout2duty))
            # device.SetWireInValue(0x14, int(args.clkout3phase))
            # device.SetWireInValue(0x15, int(args.clkout3duty))
            device.UpdateWireIns()
            trigerror = device.ActivateTriggerIn(0x40, 0)

        device.UpdateWireOuts()
        statusWire = device.GetWireOutValue(0x24)
        print('     PLL reprogrammed. Status is ', statusWire)

        # Initialize data
        self.img = np.zeros(numpix, dtype=np.uint64)
        self.scatt = np.zeros(fnum * numpix, dtype=np.uint8)
        self.goodframes = 0



        # START THE FSM ----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- -----------
        device.SetWireInValue(0x00, int(fpgaSwitches, 2))
        device.UpdateWireIns()

        # COLLECT DATA
        if getdata == True:

            BlockSize = 256  # in bytes, important to be the same as in the VHDL code otherwise data could be different
            inum = int(inum)
            # device.UpdateWireOuts()
            # MemoryCount = device.GetWireOutValue(0x26)
            # print('     Current memory count is: %d ' % MemoryCount)

            timestamp = np.zeros(inum)
            ts0 = time.time()
            for i in range(0, inum):

                device.UpdateWireOuts()
                MemoryCount = device.GetWireOutValue(0x26)
                data_out = bytearray((fnum + fignore) * 1024)  # Bytes
                TransferSize = len(data_out)
                # print('     Now transferring {} KB of data from FPGA to PC'.format(TransferSize))
                # print('status 1')

                while (MemoryCount < TransferSize):  # /8
                    device.UpdateWireOuts()
                    MemoryCount = device.GetWireOutValue(0x26)
                    # time.sleep(0.001)  # It takes 1 second to fill up the memory to 64MB, so it is useless to check 100000x per second
                    # print('status 2: memory count = %f' % MemoryCount)

                if (MemoryCount >= TransferSize):  # /8
                    code = device.ReadFromBlockPipeOut(0xa0, BlockSize, data_out)
                    # print('status 3: memory count = %f' % MemoryCount)
                    timestamp[i] = time.time() - ts0
                    print('     timestamp: for frame %i is: %f sec' % (i, timestamp[i]))

                    if code == TransferSize:
                        # #save readout data into bytearray
                        # print('     TransferSize match. Data Retrieved: %.1f kB(frames)' % float(int(code)/1024))
                        # with open(args.outputfile + '_img_' + str(i), 'wb') as f:
                        #     f.write(data_out)
                        #     # print('status 4')
                        # with open(args.outputfile + '_timestamp', 'wb') as f:
                        #     f.write(timestamp)

                        if parseenable == True:
                            # parse without saving rawdata. only save resulting images.
                            [self.img, self.scatt, self.goodframes] = parse_bytearray.ParseBytearray(numpix, fnum,
                                                                        fignore, data_out).get_data()
                            self.outputdata()  # output data for live imaging

                            # save parsed data to files
                            if saveenable:
                                with open(sdir + '\\' + sname + '_parsedraw_' + str(i), 'wb') as f:
                                    f.write(self.scatt)
                                with open(sdir + '\\' + sname + '_parsedflat_' + str(i) + 'flat', 'wb') as f:
                                    f.write(self.img)
                        else:
                            # save raw data to files
                            if saveenable:
                                with open(sdir + '\\' + sname + '_unparsed_' + str(i), 'wb') as f:
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

    def outputdata(self):
        return [self.img, self.scatt, self.goodframes]
