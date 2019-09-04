import numpy as np
import os
import time
import matplotlib.pyplot as plt


class Parse(object):

    def __init__(self, npix, datasize, ignoreframes, dir, iframe):
        start = time.time()
        print("Begin parsing.")

        fileName = os.listdir(dir)
        f = open(dir + fileName[iframe], mode="r")
        aint = np.fromfile(f, dtype=np.uint16)
        alen = len(aint)

        # find first point where addr=0 after trimming ignoreframes
        nstart = ignoreframes * npix * 2
        tempaddr = (aint[nstart]) >> 6  # rotate right by 6 to extract address, because data bits don't wrap around
        # tempaddr = (aint[nstart] & (np.power(2,17)-np.power(2,7)))>>6 #zero data and rotate right by 6 to extract address
        nn = nstart + (512 - tempaddr)  # initial starting point
        self.img = np.zeros(npix, dtype=np.uint64)
        self.scatt = np.zeros(datasize * npix, dtype=np.uint16)
        onegoodframe = np.zeros(npix, dtype=np.uint16)
        self.goodframes = 0
        # line = '{0:15b}'.format(aint[nn])

        while nn < alen - npix:
            tempaddr = (aint[
                            nn + npix]) >> 6  # rotate right by 6 to extract address, because data bits don't wrap around
            # tempaddr = (aint[nn+npix] & (np.power(2,17)-np.power(2,7)))>>6 #zero data and rotate right by 6 to extract address
            if tempaddr == 0:  # if addr(nn+npix) returns to zero, meaning data in between is intact
                onegoodframe = aint[nn:nn + npix] & int('111111', 2)
                self.scatt[self.goodframes * npix: (self.goodframes + 1) * npix] = onegoodframe
                self.img = self.img + np.uint64(onegoodframe)  # arraywise and to extract 6bit data
                nn = nn + npix  # increment nn by 512
                self.goodframes += 1
            else:  # if addr(nn+npix) is not zero, there's been a discontinuity in the data
                nn = nn + (npix - tempaddr)

        end = time.time()
        print("Parsed in " + str(round(end - start, 3)) + " s.  " + str(self.goodframes) + " of " + str(
            datasize) + " frames are intact.")


        # #plot data
        # start = time.time()
        # print("Begin plotting.")
        # plt.figure()
        #
        # plt.subplot(211)
        # plt.scatter(np.tile(range(0,npix),self.goodframes), self.scatt[0:self.goodframes*npix], color='tab:blue')
        # plt.ylim(0, 64)
        # plt.yticks(range(0,64,16))
        # plt.xlim(0, 511)
        #
        # plt.subplot(212)
        # plt.plot(self.img, color='tab:orange')
        # plt.ylim(0, self.goodframes*64) #draw to 64 to be able to see 63 limit
        # plt.xlim(0, 511)
        # plt.show()
        #
        # end = time.time()
        # print("Plotted in "+str(round(end-start,3))+" s.")

    def get_data(self):
        return [self.img, self.scatt, self.goodframes]
