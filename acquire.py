import sys
import time
import ok
import os
import argparse
import numpy as np


if __name__ == '__main__':
    #print('     This is the name of the script: ', sys.argv[0])
    #print('     Number of arguments: ', len(sys.argv))
    #print('     The arguments are: ' , str(sys.argv))


    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reset', nargs='?', default=0, type=int, help='Full reset y/n')
    parser.add_argument('-ep00', '--ep00wire', nargs='?', default=0, type=bin, help='ep00wire') #reset code
    parser.add_argument('-ep01', '--ep01wire', nargs='?', default=0, type=int, help='ep01wire') #unused
    parser.add_argument('-ep02', '--ep02wire', nargs='?', default=1, type=int, help='ep02wire') #fsm framelength in clock cycles
    parser.add_argument('-ep03', '--ep03wire', nargs='?', default=0, type=int, help='ep03wire') #fsm delay length in clock cycles
    # parser.add_argument('-ep17', '--ep17wire', nargs='?', default=1, type=int, help='ep17wire')
    # parser.add_argument('-ep18', '--ep18wire', nargs='?', default=1, type=int, help='ep18wire')
    parser.add_argument('-clkdiv', '--clkdiv', nargs='?', default=12, type=int, help='clkdivisions') #ep04: PLL freq multiplier
    parser.add_argument('-c0p', '--clkout0phase', nargs='?', default=0, type=int, help='clkout0phase')
    parser.add_argument('-c0d', '--clkout0duty', nargs='?', default=50000, type=int, help='clkout0duty')
    # parser.add_argument('-c1p', '--clkout1phase', nargs='?', default=0, type=int, help='clkout1phase')
    # parser.add_argument('-c1d', '--clkout1duty', nargs='?', default=50000, type=int, help='clkout1duty')
    # parser.add_argument('-c2p', '--clkout2phase', nargs='?', default=0, type=int, help='clkout2phase')
    # parser.add_argument('-c2d', '--clkout2duty', nargs='?', default=50000, type=int, help='clkout2duty')
    # parser.add_argument('-c3p', '--clkout3phase', nargs='?', default=0, type=int, help='clkout3phase')
    # parser.add_argument('-c3d', '--clkout3duty', nargs='?', default=50000, type=int, help='clkout3duty')
    parser.add_argument('-rpp', '--reprogpll', nargs='?', default=0, type=int, help='reprogram pll')

    parser.add_argument('-rstc', '--resetcode', nargs='?', default=7, type=int, help='Reset code')
    parser.add_argument('-ds', '--datasize', nargs='?', default=1, type=int, help='Size of datachunks in KB')
    parser.add_argument('-nimg', '--numimage', nargs='?', default=1, type=int, help='Number of snaps')
    parser.add_argument('-ff', '--flashfile', nargs='?', default=1, type=str, help='Flash file')
    parser.add_argument('-f', '--flash', nargs='?', default=0, type=int, help='Flash file')
    parser.add_argument('-o', '--outputfile', nargs='?', default=1, type=str, help='Output file')
    parser.add_argument('-get', '--getdata', nargs='?', default=0, type=int, help='Get data')
    # parser.add_argument('-off', '--setoff', nargs='?', default=0, type=int, help='Turn the pixels in the mask off')
    # parser.add_argument('-pixoff', '--pixoffmask', nargs='?', default=0, type=int, help='512b pixel off mask')



# INITIALIZATION ----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- -------
    # args = parser.parse_args()
    args, unknown = parser.parse_known_args() #unknown is for two unknown


    args.flash = 1
    args.flashfile = 'bitfile\\Nov2018_dualprobe_v1_03mmfpc_pll_intclk.bit'

    args.reprogpll = 1
    args.reset = 1
    args.resetcode = 7
    args.ep00wire = '10000000100110000'
    args.ep01wire
    args.ep02wire
    args.ep03wire

    args.clkdiv = 12
    args.clkout0duty = 50000
    args.clkout0phase = 180000

    args.getdata = 1
    args.datasize = 1000
    args.ignoreframes = 10
    args.numimage = 3
    args.outputfile = 'rawdata\\dat'

    args



    error_list = []

    # FIND AND OPEN THE OPAL KELLY (CAN ONLY RECOGNIZE SINGLE DEVICE)
    device = ok.okCFrontPanel()
    device.OpenBySerial(device.GetDeviceListSerial(0))

    # FLASH DEVICE
    if args.flash == 1:
        flerr = device.ConfigureFPGA(args.flashfile)
        print('     Flashing device with error code ', flerr)

    if device.IsFrontPanelEnabled(): # IsFrontPanelEnabled returns true if FrontPanel is detected.
        #print("     FrontPanel host interface enabled.")
        pass
    else:
        sys.stderr.write("     FrontPanel host interface not detected.")


# EXECUTION ----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- -----------

    # RESET EVERYTHING
    if args.reset == 1:
        #print('     Fully resetting device')
        error_list.append(device.SetWireInValue(0x00, int(args.resetcode)))
        device.UpdateWireIns()
        time.sleep(0.5)
        #set everything to rest
        device.SetWireInValue(0x00, int(0x00000000))
        device.UpdateWireIns()

    # WIREINS
    # device.SetWireInValue(0x01, int(args.ep01wire))
    device.SetWireInValue(0x02, int(args.ep02wire))
    device.SetWireInValue(0x03, int(args.ep03wire))
    device.SetWireInValue(0x04, int(args.clkdiv))
    device.UpdateWireIns()

    # REPROGRAM PLL
    if args.reprogpll == 1:
        device.SetWireInValue(0x05, int(args.clkout0phase))
        device.SetWireInValue(0x06, int(args.clkout0duty))
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

    # START THE FSM
    device.SetWireInValue(0x00, int(args.ep00wire,2))
    device.UpdateWireIns()

    # COLLECT DATA
    if args.getdata == 1:

        BlockSize = 256  # in bytes, important to be the same as in the VHDL code otherwise data could be different
        numimage = int(args.numimage)
        # device.UpdateWireOuts()
        # MemoryCount = device.GetWireOutValue(0x26)
        # print('     Current memory count is: %d ' % MemoryCount)

        timestamp = np.zeros(numimage);
        ts0 = time.time()
        for i in range(0, numimage):

            device.UpdateWireOuts()
            MemoryCount = device.GetWireOutValue(0x26)
            data_out = bytearray(int(args.datasize) * 1024) #Bytes
            TransferSize = len(data_out)
            #print('     Now transferring {} KB of data from FPGA to PC'.format(TransferSize))
            # print('status 1')

            while (MemoryCount < TransferSize): #/8
                device.UpdateWireOuts()
                MemoryCount = device.GetWireOutValue(0x26)
                # time.sleep(0.001)  # It takes 1 second to fill up the memory to 64MB, so it is useless to check 100000x per second
                # print('status 2: memory count = %f' % MemoryCount)

            if (MemoryCount >= TransferSize): #/8
                code = device.ReadFromBlockPipeOut(0xa0, BlockSize, data_out)
                # print('status 3: memory count = %f' % MemoryCount)
                timestamp[i] = time.time() - ts0
                print('     timestamp: for frame %i is: %f sec' % (i, timestamp[i]))

                if code == TransferSize:
                    print('     TransferSize match. Data Retrieved: %.1f kB(frames)' % float(int(code)/1024))
                    with open(args.outputfile + '_img_' + str(i), 'wb') as f:
                        f.write(data_out)
                        # print('status 4')
                    with open(args.outputfile + '_timestamp', 'wb') as f:
                        f.write(timestamp)
                else:
                    print('     TransferSize doesnt match. Amount of data retrieved from Pipe Out is %d Bytes' % code)
                    print('     Do not write file!')
                    sys.stderr.write("     Data was not retrieved correctly. Error code returned is %d Bytes" % code)
                    # print('status 5')

                # reset RAM
                print('     Current memory count is: %d ' % MemoryCount)
                device.SetWireInValue(0x00, int(0x00000007))
                device.UpdateWireIns()
                device.SetWireInValue(0x00, int(args.ep00wire,2))
                device.UpdateWireIns()


                device.UpdateWireOuts()
                MemoryCount = device.GetWireOutValue(0x26)
                # print('status 6')
