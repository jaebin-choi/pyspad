import sys
import numpy as np
import ok
import threading
import time

instanceLock = threading.RLock()
_instance = None
BlockSize = 256

def Instance():
    instanceLock.acquire()
    global _instance
    if _instance is None:
        _instance = OKInstance()
    instanceLock.release()
    return _instance


class OKInstance(ok.okCFrontPanel):
    def __init__(self):
        super(OKInstance, self).__init__()

        # FIND AND OPEN THE OPAL KELLY (CAN ONLY RECOGNIZE SINGLE DEVICE) ----------- ----------- ----------- ----------
        # self.device = ok.okCFrontPanel()
        # self.device.OpenBySerial(self.device.GetDeviceListSerial(0))

    def flash(self, bitfile):
        flerr = self.ConfigureFPGA(bitfile)
        if flerr == 0:
            print('     Opal Kelly Flash Successful.')
        else:
            print('     Opal Kelly Flash with error code ', flerr)

        if self.IsFrontPanelEnabled():  # IsFrontPanelEnabled returns true if FrontPanel is detected.
            print("     FrontPanel host interface enabled.")
            pass
        else:
            sys.stderr.write("     FrontPanel host interface NOT detected.")

    def reset(self, rstcode):
        # RESET EVERYTHING
        error_list = []
        print('     Resetting Opal Kelly.')
        error_list.append(self.SetWireInValue(0x00, int(rstcode)))  # set to reset state
        self.UpdateWireIns()
        time.sleep(0.1)

        # set everything to rest
        self.SetWireInValue(0x00, int(0x00000000))  # set to rest state
        self.UpdateWireIns()

    def reprogPLL(self, flen, clkdiv, phase, duty, fpgaSwitches):
        # WIREINS
        # self.SetWireInValue(0x01, int(ep01wire)) #not used
        self.SetWireInValue(0x02, flen)
        # self.SetWireInValue(0x03, int(ep03wire))
        self.SetWireInValue(0x04, clkdiv)
        self.SetWireInValue(0x05, phase)
        self.SetWireInValue(0x06, duty)
        # self.SetWireInValue(0x07, int(args.clkout1phase))
        # self.SetWireInValue(0x08, int(args.clkout1duty))
        # self.SetWireInValue(0x09, int(args.clkout2phase))
        # self.SetWireInValue(0x10, int(args.clkout2duty))
        # self.SetWireInValue(0x14, int(args.clkout3phase))
        # self.SetWireInValue(0x15, int(args.clkout3duty))
        self.UpdateWireIns()
        trigerror = self.ActivateTriggerIn(0x40, 0)

        self.UpdateWireOuts()
        statusWire = self.GetWireOutValue(0x24)
        print('     PLL reprogrammed. Status is ', statusWire)

        # Reset RAM and restart FSM
        self.SetWireInValue(0x00, int(0x00000007))  # set to reset state
        self.UpdateWireIns()
        self.SetWireInValue(0x00, int(fpgaSwitches, 2))  # start FSM
        self.UpdateWireIns()
        print('     FSM initiated.')

        ###############################################################################################################
    def acquireDataSingle(self, fnum, fignore, fpgaSwitches):

        # Initialize data
        # img = np.zeros(npix, dtype=np.uint64)
        # scatt = np.zeros(fnum * npix, dtype=np.uint8)
        # goodframes = 0

        self.UpdateWireOuts()
        MemoryCount = self.GetWireOutValue(0x26)
        data_out = bytearray((fnum + fignore) * 1024)  # Bytes
        TransferSize = len(data_out)
        # print('     Now transferring {} KB of data from FPGA to PC'.format(TransferSize))
        # print('status 1')

        # accumulate FPGA memory until MemoryCount is larger than TransferSize
        while MemoryCount < TransferSize:  # /8
            self.UpdateWireOuts()
            MemoryCount = self.GetWireOutValue(0x26)

        # pipe out data
        code = self.ReadFromBlockPipeOut(0xa0, BlockSize, data_out)
        timestamp = time.time()  # timestamp when data finished reading
        if code == TransferSize:
            # save readout data into bytearray
            # print('     TransferSize match. Data Retrieved: %.1f kB(frames)' % float(int(code) / 1024))
            # with open(tsdir + '\\' + sname + '_timestamp', 'wb') as f:
            #     f.write(bytes(timestamp))

            # with open(sdir + '\\' + sname + '_unparsed_i' + str(ii), 'wb') as f:
            #     f.write(data_out)
            return data_out, timestamp
        else:
            print('     TransferSize doesnt match. Amount of data retrieved from Pipe Out is %d Bytes' % code)
            print('     Do not write file!')
            sys.stderr.write(
                "     Data was not retrieved correctly. Error code returned is %d Bytes" % code)
            # print('status 5')

        # Reset RAM and restart FSM
        self.SetWireInValue(0x00, int(0x00000007))  # set to reset state
        self.UpdateWireIns()
        self.SetWireInValue(0x00, int(fpgaSwitches, 2))  # start FSM
        self.UpdateWireIns()

        # self.device.UpdateWireOuts()
        # MemoryCount = self.device.GetWireOutValue(0x26)  # should be zero

