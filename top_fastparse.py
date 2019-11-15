
import acquire_bytearray_extinput
import time
import numpy as np

if __name__ == '__main__':


    flash = True
    reset = True
    reprogpll = True
    parseenable = False  # parsing takes ~200ms
    saveenable = True  # saving takes ~50ms
    getdata = True

    numpix = '512'
    bitfile = 'bitfile\\Nov2018_dualprobe_v1_03mmfpc_pll_intclk.bit'
    rstcode = '0111'
    fpgaSwitches = '10000000100110000'  # reset code
    clkdiv = '12'
    duty = '50000'
    phase = '180000'
    flen = '100'  # framelength
    fignore = '10'
    fnum = '1000'
    inum = '10'
    sdir = 'rawdata'
    sname = 'sampleoutput'


    # AcqOK returns the array for each frame, and does it one last time in the end. Don't know if this is a problem. JC 11/12
    [img, scatt, goodframes] = acquire_bytearray_extinput.AcqOK(flash, reset, reprogpll, parseenable, saveenable, getdata,
         numpix, bitfile, rstcode, fpgaSwitches, clkdiv, duty, phase, flen, fignore, fnum, inum, sdir, sname).outputdata()

    # #plot data
    # start = time.time()
    # print("Begin plotting.")
    # plt.figure()
    #
    # plt.subplot(211)
    # plt.scatter(np.tile(range(0, numpix), goodframes), scatt[0:goodframes*numpix], color='tab:blue')
    # plt.ylim(0, 64)
    # plt.yticks(range(0, 64, 16))
    # plt.xlim(0, 511)
    #
    # plt.subplot(212)
    # plt.plot(img, color='tab:orange')
    # plt.ylim(0, goodframes*64) #draw to 64 to be able to see 63 limit
    # plt.xlim(0, 511)
    # plt.show()
    #
    # end = time.time()
    # print("Plotted in "+str(round(end-start, 3))+" s.")


    # # plot if plotenabled
    # if plotenable:
    #     fig = plt.figure()
    #     ax = fig.add_subplot(111)
    #     y = np.zeros(numpix, dtype=np.uint64)
    #     li, = ax.plot(range(1, numpix + 1), y)
    #     # ax.relim()
    #     # ax.autoscale_view(True, True, True)
    #     fig.canvas.draw()
    #     plt.show(block=False)
    #
    #     # update y value in the plot if plotenabled
    #     li.set_ydata(self.img)
    #     fig.canvas.draw()