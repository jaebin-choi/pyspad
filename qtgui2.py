from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSlot
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
                             QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
                             QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
                             QVBoxLayout, QWidget, QButtonGroup)
import pyqtgraph as pg
import numpy as np
import acquire_bytearray_extinput

# import matplotlib.pyplot as plt


# pg.setConfigOption('background', 'w')


# noinspection PyAttributeOutsideInit
class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        # create widgets
        self.originalPalette = QApplication.palette()
        self.createControlGroupBox()
        self.createProgressBar()
        self.plot1 = pg.PlotWidget(name='Plot1')
        self.plot2 = pg.PlotWidget(name='Plot2')
        self.plot3 = pg.PlotWidget(name='Plot3')

        # place different widgets on mainLayout
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.controlGroupBox, 0, 0)
        mainLayout.addWidget(self.plot1, 1, 0)
        mainLayout.addWidget(self.plot2, 0, 1)
        mainLayout.addWidget(self.plot3, 1, 1)
        mainLayout.addWidget(self.progressBar, 2, 0, 1, 2)

        #box sizes
        self.controlGroupBox.setMinimumWidth(600)
        self.plot2.setMinimumWidth(1000)
        self.plot2.setMinimumHeight(200)
        self.plot3.setMinimumWidth(1000)
        self.plot2.setMinimumHeight(200)
        self.setLayout(mainLayout)
        self.setWindowTitle("SPAD Probe Acquisition")

        # set plot axes
        self.setPlotWidget(self.plot1, 0, 512, 0, 512, 'Pixel', 'Counts', '', '')

        # connect buttons
        self.btnRun.clicked.connect(self.ifbtnRunClicked)
        self.btnFlash.clicked.connect(self.ifbtnFlashClicked)

        # declare variables (will be integrated)
        self.Flash = int(self.tglFlash.isChecked())
        self.Reset = int(self.tglReset.isChecked())
        self.ReprogPLL = int(self.tglReprogPLL.isChecked())
        self.Parse = int(self.tglParse.isChecked())
        self.Save = int(self.tglSave.isChecked())

        self.npix = 512
        self.bitfile = self.LEbitfile.text()
        self.rstcode = self.LErstcode.text()
        self.fpgaSwitches = self.LEswitch.text()  # ep00wire
        self.fvco = self.LEfvco.text()
        self.frep = self.LEfrep.text()
        self.duty = self.LEduty.text()
        self.phase = self.LEphase.text()
        self.flen = self.LEflen.text()  # ep02wire. framelength
        self.fignore = self.LEfignore.text()
        self.fnum = self.LEfnum.text()  # datasize
        self.inum = self.LEinum.text()
        self.tacq = self.LEtacq.text()
        self.sdir = self.LEsdir.text()
        self.sname = self.LEsname.text()
        self.sidx = self.LEsidx.text()

        self.clkdiv = round(int(self.fvco)/int(self.frep))


    @pyqtSlot() ##################################################### START HERE 11/14. MAKE
    def ifbtnFlashClicked(self):
        flash = True
        reset = True
        reprogpll = False
        parseenable = False
        saveenable = False
        getdata = False

        [img, scatt, goodframes] = acquire_bytearray_extinput.AcqOK(flash, reset, reprogpll, parseenable, saveenable, getdata,
            self.numpix, self.bitfile, self.rstcode, self.fpgaSwitches, self.clkdiv, self.duty, self.phase,
            self.flen, self.fignore, self.fnum, self.inum, self.sdir, self.sname).outputdata()




    @pyqtSlot()
    def ifbtnRunClicked(self):
        import parse




        # get data from opal kelly


        # fetch data from parse module
        [self.img, self.scatt, self.goodframes] = parse.Parse(self.npix, self.flen, self.fignore, self.sdir, 4).get_data()

        # update plots with parsed data
        self.plot2.plot(self.img)  # flattened image
        self.plot3.plot(np.tile(range(0, self.npix), self.goodframes), self.scatt[0:self.goodframes * self.npix])  # raw count scatterplot

        self.setPlotWidget(self.plot2, 0, 512, 0, max(self.img), 'Pixel', 'Accumulated Counts', '', '')
        self.setPlotWidget(self.plot3, 0, 512, 0, max(self.scatt), 'Pixel', 'Flattened Counts', '', '')


    def setPlotWidget(self, plot, xmin, xmax, ymin, ymax, xlabel, ylabel, xunit, yunit):
        plot.setLabel('bottom', xlabel, units=xunit)
        plot.setLabel('left', ylabel, units=yunit)
        plot.setXRange(xmin, xmax)
        plot.setYRange(ymin, ymax)

    def advanceProgressBar(self):
        curVal = self.progressBar.value()
        maxVal = self.progressBar.maximum()
        self.progressBar.setValue(curVal + (maxVal - curVal) / 100)

    def createControlGroupBox(self):
        self.controlGroupBox = QGroupBox("Controls")

        # create lineEdits
        self.LEbitfile = QLineEdit('bitfile\\bitfilename.bit')
        self.LErstcode = QLineEdit('7')
        self.LEswitch = QLineEdit('10000000100110000')
        self.LEfvco = QLineEdit('960')
        self.LEfrep = QLineEdit('10')
        self.LEduty = QLineEdit('50')
        self.LEphase = QLineEdit('180')
        self.LEflen = QLineEdit('1000')
        self.LEfignore = QLineEdit('10')
        self.LEfnum = QLineEdit('1000')
        self.LEinum = QLineEdit('10')  # or infinite
        self.LEtacq = QLineEdit('?')
        self.LEsdir = QLineEdit('D:\\dropbox\\Dropbox\\Projects\\SpadProbe\\201902_caltechGcamp\\code package\\outfile\\0223\\0223_recording_LP57\\')
        self.LEsname = QLineEdit('sample')
        self.LEsidx = QLineEdit('1')

        # create text labels
        Tbitfile = QLabel('Bitfile'); Tbitfile.setBuddy(self.LEbitfile)
        Trstcode = QLabel('Rst Code'); Trstcode.setBuddy(self.LErstcode)
        Tswitch = QLabel('FPGA Switches'); Tswitch.setBuddy(self.LEswitch)
        Tclock = QLabel('Clock')
        Tfvco = QLabel('Fvco'); Tfvco.setBuddy(self.LEfvco)
        Tfrep = QLabel('Rep Rate'); Tfrep.setBuddy(self.LEfrep)
        Tduty = QLabel('Duty Cycle'); Tduty.setBuddy(self.LEduty)
        Tphase = QLabel('Phase'); Tphase.setBuddy(self.LEphase)
        Tacquire = QLabel('Acquire')
        Tflen = QLabel('Frame length'); Tflen.setBuddy(self.LEflen)
        Tfignore = QLabel('Pass length'); Tfignore.setBuddy(self.LEfignore)
        Tfnum = QLabel('#Frames'); Tfnum.setBuddy(self.LEfnum)
        Tinum = QLabel('#Images'); Tinum.setBuddy(self.LEinum)
        Ttacq = QLabel('Tacq/Img'); Ttacq.setBuddy(self.LEtacq)
        Tsave = QLabel('Save')
        Tsdir = QLabel('Dir'); Tsdir.setBuddy(self.LEsdir)
        Tsname = QLabel('Name'); Tsname.setBuddy(self.LEsname)
        Tsidx = QLabel('Index'); Tsidx.setBuddy(self.LEsidx)

        # create buttons
        self.btnFlash = QPushButton("Flash"); self.btnFlash.setDefault(True)
        self.btnReset = QPushButton("Reset"); self.btnReset.setDefault(True)
        self.btnReprogPLL = QPushButton("rePLL"); self.btnReprogPLL.setDefault(True)
        btngroup1 = QButtonGroup(self.controlGroupBox); btngroup1.setExclusive(False)
        self.tglFlash = QRadioButton("Flash"); self.tglFlash.setChecked(False)
        self.tglReset = QRadioButton("Reset"); self.tglReset.setChecked(True)
        self.tglReprogPLL = QRadioButton("reprogram PLL"); self.tglReprogPLL.setChecked(False)
        self.tglParse = QRadioButton("Parse"); self.tglParse.setChecked(False)
        self.tglSave = QRadioButton("Save"); self.tglSave.setChecked(True)
        btngroup1.addButton(self.tglFlash)
        btngroup1.addButton(self.tglReset)
        btngroup1.addButton(self.tglReprogPLL)
        btngroup1.addButton(self.tglParse)
        btngroup1.addButton(self.tglSave)
        self.btnRun = QPushButton("Run"); self.btnRun.setDefault(False)

        # create layout
        boxlayout = QVBoxLayout()

        line = [Tbitfile, self.LEbitfile, self.btnFlash]
        size = [1, 100, 1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Trstcode, self.LErstcode, Tswitch, self.LEswitch, self.btnReset, self.btnReprogPLL]
        size = [1, 1, 1, 80, 1, 1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Tclock, Tfvco, self.LEfvco, Tfrep, self.LEfrep, Tduty, self.LEduty, Tphase, self.LEphase]
        size = [1, 0, 1, 0, 1, 0, 1, 0, 1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Tacquire, Tflen, self.LEflen, Tfignore, self.LEfignore, Tfnum, self.LEfnum, Tinum, self.LEinum, Ttacq, self.LEtacq]
        size = [2,1,2,1,2,1,2,1,2,1,2]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Tsave, Tsdir, self.LEsdir, Tsname, self.LEsname, Tsidx, self.LEsidx]
        size = [2,1,100,1,30,1,1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [self.tglFlash, self.tglReset, self.tglReprogPLL, self.tglParse, self.tglSave, self.btnRun]
        size = [1,1,1,1,1,100]
        self.layoutSingleLine(boxlayout, line, size)

        self.controlGroupBox.setLayout(boxlayout)


    def layoutSingleLine(self, boxlayout, line, size):
        hlayout = QHBoxLayout()
        for i in range(len(line)):
            hlayout.addWidget(line[i], size[i])
        boxlayout.addLayout(hlayout)

    def createProgressBar(self):
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 10000)
        self.progressBar.setValue(0)

        timer = QTimer(self)
        timer.timeout.connect(self.advanceProgressBar)
        timer.start(1000)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName('SPADProbeAcquire')
    app.setStyle("fusion")
    gallery = WidgetGallery()
    gallery.resize(1200, 600)
    gallery.show()
    sys.exit(app.exec_())
