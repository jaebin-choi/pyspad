# parse directly from bytearray without saving and opening bytearray. Put directly into
import numpy as np
import time



def twobytes2data(bytearraydata, ii):
    return bytearraydata[ii] & 0b00111111


def twobytes2addr(bytearraydata, ii):
    return bytearraydata[ii + 1] * 4 + (bytearraydata[ii] >> 6)


class ParseBytearray(object):

    def __init__(self, numpix, datasize, ignoreframes, bytearraydata):
        start = time.time()
        # print("Begin parsing.")

        alen = len(bytearraydata) #length of array is datasize*numpix*2. (2 because two bytes make one frame!)
        # print(alen)

        # find first point where addr=0 after trimming ignoreframes
        nstart = ignoreframes * numpix*2  # times 2 because every frame is 2 bytes
        tempaddr = twobytes2addr(bytearraydata, nstart)
        nbyte = nstart + (numpix-tempaddr)*2  # start data parsing from this byte index
        # print(twobytes2addr(bytearraydata, nbyte)) # check that this is zero

        self.img = np.zeros(numpix, dtype=np.uint64)
        self.scatt = np.zeros(datasize * numpix, dtype=np.uint8)
        self.goodframes = 0
        onegoodframe = np.zeros(numpix, dtype=np.uint8)



        while nbyte < alen - numpix*2:  # times 2 because every pixel is 16 bits, hence 2 bytes
            tempaddr = twobytes2addr(bytearraydata, nbyte + numpix*2)
            if tempaddr == 0:  # if addr(nbyte+numpix) returns to zero, meaning data in between is intact
                for i in range(numpix):
                    onegoodframe[i] = twobytes2data(bytearraydata, nbyte+i*2)
                # print(self.goodframes * numpix)
                self.scatt[self.goodframes * numpix: (self.goodframes + 1) * numpix] = onegoodframe
                self.img = self.img + onegoodframe
                nbyte = nbyte + numpix*2  # increment nbyte by 512
                self.goodframes += 1
                # print(self.goodframes)
            else:  # if addr(nbyte+numpix) is not zero, there's been a discontinuity in the data
                nbyte = nbyte + (numpix-tempaddr)*2

        end = time.time()
        print("     Parsed in " + str(round(end - start, 3)) + " s.  " + str(self.goodframes) + " of " + str(
            datasize) + " frames are intact.")



    def get_data(self):
        return [self.img, self.scatt, self.goodframes]
