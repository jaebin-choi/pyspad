import numpy as np
import time


class Parse(object):

    def __init__(self, npix, datasize, ignoreframes, fullfilepath):
        # start timer
        start = time.time()
        # print("Begin parsing.")

        # convert strings into arrays
        npix = int(npix)
        datasize = int(datasize)
        ignoreframes = int(ignoreframes)

        # open file, convert 2 bytes (16 bits) to uint16 array
        with open(fullfilepath, mode="r") as f:  # changed to 'with open' to close file handle every time
        # f = open(fullfilepath, mode="r")
            aint = np.fromfile(f, dtype=np.uint16)
        alen = len(aint)

        # find first point where addr=0 after trimming ignoreframes
        nstart = ignoreframes * npix
        tempaddr = (aint[nstart]) >> 6  # rotate right by 6 to extract address, because data bits don't wrap around
        nn = nstart + (512 - tempaddr)  # initial starting point
        self.img = np.zeros(npix, dtype=np.uint64)
        self.scatt = np.zeros(datasize * npix, dtype=np.uint16)
        onegoodframe = np.zeros(npix, dtype=np.uint16)
        self.goodframes = 0

        while nn < alen - npix:
            tempaddr = (aint[nn + npix]) >> 6  # rotate right by 6 to extract address
            if tempaddr == 0:  # if addr(nn+npix) returns to zero, meaning data in between is intact
                onegoodframe = aint[nn:nn + npix] & int('111111', 2)
                self.scatt[self.goodframes * npix: (self.goodframes + 1) * npix] = onegoodframe
                self.img = self.img + np.uint64(onegoodframe)  # arraywise and to extract 6bit data
                nn = nn + npix  # increment nn by 512
                self.goodframes += 1
            else:  # if addr(nn+npix) is not zero, there's been a discontinuity in the data
                nn = nn + (npix - tempaddr)

        end = time.time()
        # print("Parsed in " + str(round(end - start, 3)) + " s.  " + str(self.goodframes) + " of " + str(
        #     datasize) + " frames are intact.")

    def get_data(self):
        return [self.img, self.scatt, self.goodframes]
