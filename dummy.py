
import os

import parse_bytearray
import parse_singledat

here = os.getcwd() + '\\pyspad\\rawdata\\'
files = os.listdir(here)
for i in range(0, len(files)):
    files[i] = here + files[i]

for i in files:
    i = here + i

[here + s for s in files]
files2 = sorted(files, key=os.path.getmtime)
files2[-1]


npix = 512
fnum = 1000
fignore = 10
newest = 'D:\\dropbox\\Dropbox\\Projects\\SpadProbe\\git\\pyspad\\rawdata\\sample0001_unparsed_9'

[img, scatt, goodframes] = parse_singledat.Parse(npix, fnum, fignore, newest).get_data()


