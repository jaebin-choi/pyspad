import numpy as np
import os
import time
import matplotlib.pyplot as plt

ignoreframes = 10
npix = 512
datasize = 1000

dir = 'rawdata'
fileName = os.listdir(dir)
header = 'dat'
#curfile = dir + '\\' + fileName[1]
curfile = 'D:\\dropbox\\Dropbox\\Projects\\SpadProbe\\201907_caltech5\\codepackage_aftertrip\\rawdata\\jul31_0610asp1_m1_shankout00_chunk_0'

start = time.time()
print("Begin parsing.")

f = open(curfile, mode="r")
aint = np.fromfile(f, dtype=np.uint16)
alen = len(aint)
#addr = bytearray(alen) #bytearray means only upto 256
#counts = bytearray(alen)

#find first point where addr=0 after trimming ignoreframes
nstart = ignoreframes*npix*2
tempaddr = (aint[nstart])>>6 #rotate right by 6 to extract address, because data bits don't wrap around
#tempaddr = (aint[nstart] & (np.power(2,17)-np.power(2,7)))>>6 #zero data and rotate right by 6 to extract address
nn = nstart+(512-tempaddr) #initial starting point
img = np.zeros(npix, dtype=np.uint64)
scatt = np.zeros(datasize*npix, dtype=np.uint16)
onegoodframe = np.zeros(npix, dtype=np.uint16)

goodframes = 0
#line = '{0:15b}'.format(aint[nn])

while nn<alen-npix:
    tempaddr = (aint[nn+npix])>>6 #rotate right by 6 to extract address, because data bits don't wrap around
    #tempaddr = (aint[nn+npix] & (np.power(2,17)-np.power(2,7)))>>6 #zero data and rotate right by 6 to extract address
    if tempaddr==0: #if addr(nn+npix) returns to zero, meaning data in between is intact
        onegoodframe = aint[nn:nn+npix] & int('111111',2)
        scatt[goodframes*npix : (goodframes+1)*npix] = onegoodframe
        img = img + np.uint64(onegoodframe) #arraywise and to extract 6bit data
        nn = nn+npix #increment nn by 512
        goodframes +=1
    else: #if addr(nn+npix) is not zero, there's been a discontinuity in the data
        nn = nn+(npix-tempaddr)


end = time.time()
print("Parsed in "+str(round(end-start,3))+" s.  "+str(goodframes)+" of "+str(datasize)+" frames are intact.")


#verify raw data without parsing
# for nn in range(0, alen):
#     line = '{0:15b}'.format(aint[nn])
#     addr[nn] = 2**8*return0ifempty(line[0]) + return0ifempty(line[1:9])
#     counts[nn] = int(line[-6:],2) #doesn't need mk_int because it is at the end


#plot flattened 512-pixel image
# plt.plot()
# plt.plot(img, color='tab:orange')
# #bottom, top = plt.ylim()
# plt.ylim(0, goodframes*64) #draw to 64 to be able to see 63 limit
# plt.xlim(0, 511)
# plt.show()


#plot parsed data
start = time.time()
print("Begin plotting.")

# plt.figure()
#
# plt.subplot(211)
# plt.scatter(np.tile(range(0,npix),goodframes), scatt[0:goodframes*npix], color='tab:blue')
# plt.ylim(0, 64)
# plt.yticks(range(0,64,16))
# plt.xlim(0, 511)
#
# plt.subplot(212)
# plt.plot(img, color='tab:orange')
# plt.ylim(0, goodframes*64) #draw to 64 to be able to see 63 limit
# plt.xlim(0, 511)

end = time.time()
print("Plotted in "+str(round(end-start,3))+" s.")


plt.show()


