import ok
import sys
import time
import numpy as np

BlockSize = 256  # in bytes, important to be the same as in the VHDL code otherwise data could be different


class ManageOK(object):
    def __init__(self, enflash, enreset, enreprogpll, interrupted,
        npix, bitfile, rstcode, fpgaSwitches, clkdiv, duty, phase, flen, fignore, fnum, inum, sdir, sname, tsdir):
        # expected data types are..
        # bool for: enflash, enreset, enreprogpll
        # str for: bitfile, rstcode, fpgaSwitches
        # int for: flen, clkdiv, phase, duty

        # FIND AND OPEN THE OPAL KELLY (CAN ONLY RECOGNIZE SINGLE DEVICE) ----------- ----------- ----------- ----------
        self.device = ok.okCFrontPanel()
        self.device.OpenBySerial(self.device.GetDeviceListSerial(0))

        # FLASH DEVICE
        if enflash == 1:
            flerr = self.device.ConfigureFPGA(bitfile)
            if flerr == 0:
                print('     Opal Kelly Flash Successful')
            else:
                print('     Opal Kelly Flash with error code ', flerr)

            if self.device.IsFrontPanelEnabled():  # IsFrontPanelEnabled returns true if FrontPanel is detected.
                print("     FrontPanel host interface enabled.")
                pass
            else:
                sys.stderr.write("     FrontPanel host interface NOT detected.")

        # RESET EVERYTHING
        error_list = []
        if enreset == 1:
            # print('     Fully resetting device')
            error_list.append(self.device.SetWireInValue(0x00, int(rstcode)))
            self.device.UpdateWireIns()
            time.sleep(0.5)
            # set everything to rest
            self.device.SetWireInValue(0x00, int(0x00000000))
            self.device.UpdateWireIns()

            # WIREINS
            # self.device.SetWireInValue(0x01, int(ep01wire)) #not used
            self.device.SetWireInValue(0x02, flen)
            # self.device.SetWireInValue(0x03, int(ep03wire))
            self.device.SetWireInValue(0x04, clkdiv)
            self.device.UpdateWireIns()

        # REPROGRAM PLL
        if enreprogpll == 1:
            self.device.SetWireInValue(0x05, phase)
            self.device.SetWireInValue(0x06, duty)
            # self.device.SetWireInValue(0x07, int(args.clkout1phase))
            # self.device.SetWireInValue(0x08, int(args.clkout1duty))
            # self.device.SetWireInValue(0x09, int(args.clkout2phase))
            # self.device.SetWireInValue(0x10, int(args.clkout2duty))
            # self.device.SetWireInValue(0x14, int(args.clkout3phase))
            # self.device.SetWireInValue(0x15, int(args.clkout3duty))
            self.device.UpdateWireIns()
            trigerror = self.device.ActivateTriggerIn(0x40, 0)

            self.device.UpdateWireOuts()
            statusWire = self.device.GetWireOutValue(0x24)
            print('     PLL reprogrammed. Status is ', statusWire)

        # START THE FSM
        self.device.SetWireInValue(0x00, int(fpgaSwitches, 2))
        self.device.UpdateWireIns()



        ###############################################################################################################
        # Data Acquisition
        timestamp = np.zeros(inum)
        ts0 = time.time()
        # interrupted = False

        for ii in range(0, inum):

            if interrupted:
                break

            # Initialize data
            # img = np.zeros(npix, dtype=np.uint64)
            # scatt = np.zeros(fnum * npix, dtype=np.uint8)
            # goodframes = 0

            self.device.UpdateWireOuts()
            MemoryCount = self.device.GetWireOutValue(0x26)
            data_out = bytearray((fnum + fignore) * 1024)  # Bytes
            TransferSize = len(data_out)
            # print('     Now transferring {} KB of data from FPGA to PC'.format(TransferSize))
            # print('status 1')

            while MemoryCount < TransferSize:  # /8
                self.device.UpdateWireOuts()
                MemoryCount = self.device.GetWireOutValue(0x26)
                # print('status 2: memory count = %f' % MemoryCount)

            code = self.device.ReadFromBlockPipeOut(0xa0, BlockSize, data_out)
            # print('status 3: memory count = %f' % MemoryCount)

            timestamp[ii] = time.time() - ts0
            print('     timestamp: for frame %i is: %f sec' % (ii, timestamp[ii]))

            if code == TransferSize:
                # #save readout data into bytearray
                print('     TransferSize match. Data Retrieved: %.1f kB(frames)' % float(int(code) / 1024))
                # with open(args.outputfile + '_img_' + str(i), 'wb') as f:
                #     f.write(data_out)
                #     # print('status 4')
                with open(tsdir + '\\' + sname + '_timestamp', 'wb') as f:
                    f.write(bytes(timestamp))

                with open(sdir + '\\' + sname + '_unparsed_i' + str(ii), 'wb') as f:
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
                self.device.SetWireInValue(0x00, int(0x00000007))
                self.device.UpdateWireIns()
                self.device.SetWireInValue(0x00, int(fpgaSwitches, 2))
                self.device.UpdateWireIns()

                self.device.UpdateWireOuts()
                MemoryCount = self.device.GetWireOutValue(0x26)
                # print('status 6')


