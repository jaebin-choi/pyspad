


import os
from pathlib import Path
import time
import numpy as np
#import pyqtgraph as pg
#from PyQt5.QtCore import QTimer, pyqtSlot
#from PyQt5.QtWidgets import (QApplication, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
#                             QPushButton, QRadioButton, QVBoxLayout, QButtonGroup, QProgressBar, QMessageBox)
import parse_singledat2


sdir = "rawdata"
pathnow = Path(os.getcwd()) / sdir
files = os.listdir(str(pathnow))
for i in range(0, len(files)):
    files[i] = str(pathnow / files[i])
files = sorted(files, key=os.path.getmtime, reverse=True)

npix = 512
fnum = 100
fignore = 10
allImg = np.zeros((len(files),npix), dtype=np.uint64)
for i in range(0, len(files)):
    newest = files[i]
    [img, scatt, goodframes] =\
                            parse_singledat2.Parse(npix, fnum, fignore, newest).get_data()
    allImg[i][0:] = img

#with open(pathnow + '\\' + 'parsedData', 'wb') as f:
with open('parsedData', 'wb') as f:
    f.write(allImg)




pathTS = Path("/Users/jchoi/Dropbox/Projects/SpadProbe/202102_videotest_flashlight/pyspad006data_movingFlashLight/timestamp")
ts = np.zeros(1000, dtype=np.uint64)

with open(self.tsdir + '\\' + self.sname + '_timestamp' + str(self.sidx).zfill(3), 'wb') as f:
    f.write(bytes(timestamp))















