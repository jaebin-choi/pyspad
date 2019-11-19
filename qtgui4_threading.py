import glob
import threading
import time
import numpy as np
from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSlot, QThread, QObject
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
                             QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
                             QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
                             QVBoxLayout, QWidget, QButtonGroup)
import pyqtgraph as pg
# pg.setConfigOption('background', 'w')

import Constants
import PlotRefresher
import acquire_bytearray_extinput
import acquire_bytearray_nooutput
import os
import parse_singledat

constants = Constants.Instance()


class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        # initialize GUI
        self.initializeGUI()

        # connect buttons
        self.btnRun.clicked.connect(self.ifbtnRunClicked)
        self.btnFlash.clicked.connect(self.ifbtnFlashClicked)
        self.btnReset.clicked.connect(self.ifbtnResetClicked)
        self.btnStop.clicked.connect(self.ifbtnStopClicked)

        # global parameters upon initiation
        self.sidx = 1
        self.npix = 512

        # declare locks
        self.datalock = threading.RLock()  # only blocks if the lock is held by ANOTHER thread

        # run side thread
        self.sidethreadinstance = threading.Thread(target=self.sideThread)
        self.stopsidethreadflag = threading.Event()

        # add to main thread timer
        self.mainThreadTimer = QTimer(self)

    ## THREADING #######################################################################################################

    # sideThread: find most recent file and parse it.
    def sideThread(self):
        print('run sideThread')

        while not self.stopsidethreadflag.is_set():
            newest = self.getLatestFile()
            print(newest)
            self.datalock.acquire()
            [self.img, self.scatt, self.goodframes] =\
                parse_singledat.Parse(self.npix, self.fnum, self.fignore, newest).get_data()
            self.datalock.release()

        print('stopped sideThread')

    def getLatestFile(self):
        print(self.sdir)
        pathnow = os.getcwd() + '\\' + self.sdir + '\\'
        files = os.listdir(pathnow)
        for i in range(0, len(files)):
            files[i] = pathnow + files[i]
        files2 = sorted(files, key=os.path.getmtime)
        newest = files2[-1]
        return newest

    def startSideThread(self):
        # create sidethread if it doesn't exist already
        if not self.sidethreadinstance.isAlive():
            print('creating sidethread')
            self.sidethreadinstance = threading.Thread(target=self.sideThread)
            self.stopsidethreadflag.clear()
        else:
            print('sidethread has already been created')

        # run side thread instance after creating it
        try:
            self.sidethreadinstance.start()
        except RuntimeError as e:
            print('sidethread is already running')
        else:
            self.stopsidethreadflag.clear()

    def stopSideThread(self):
        self.stopsidethreadflag.set()

    def mainThread(self):
        self.updatePlots()

    def updatePlots(self):
        self.datalock.acquire()
        self.plot2.plot(self.img)  # flattened image
        self.plot3.plot(np.tile(range(0, self.npix), self.goodframes),
                        self.scatt[0:self.goodframes * self.npix])  # raw count scatterplot
        self.setPlotWidget(self.plot2, 0, 512, 0, max(self.img), 'Pixel', 'Accumulated Counts', '', '')
        self.setPlotWidget(self.plot3, 0, 512, 0, max(self.scatt), 'Pixel', 'Flattened Counts', '', '')
        self.datalock.release()

    def startMainThread(self):
        self.sidx = 1
        if self.mainThreadTimer.isActive():
            self.mainThreadTimer.stop()
        self.mainThreadTimer.timeout.connect(self.mainThread)
        self.mainThreadTimer.setInterval(constants.MAIN_UPDATING_INTERVAL)
        self.mainThreadTimer.setSingleShot(False)
        self.mainThreadTimer.start()

    def stopMainThread(self):
        self.mainThreadTimer.stop()

    def closeEvent(self, event):
        ''' Override function
            Re-define what to do at user hit quitting the GUI
        '''
        print("Killing auto-updating threads ...")
        self.stopMainThread()
        print("stopped main thread timer")
        self.stopSideThread()
        print("stopped side thread")
        # Wait for the opal kelly components to clean itself properly
        # Otherwise core dump is likely to be raised
        time.sleep(1)
        event.accept()

    #########################################################################################################

    def initializeGUI(self):
        # create widgets
        self.originalPalette = QApplication.palette()
        self.createControlGroupBox()
        self.createProgressBar()
        self.plot1 = pg.PlotWidget(name='Plot1')
        self.plot2 = pg.PlotWidget(name='Plot2')
        self.plot3 = pg.PlotWidget(name='Plot3')

        # self.setPlot1Handle(self.plot1)

        # place different widgets on mainLayout
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.controlGroupBox, 0, 0)
        self.mainLayout.addWidget(self.plot1, 1, 0)
        self.mainLayout.addWidget(self.plot2, 0, 1)
        self.mainLayout.addWidget(self.plot3, 1, 1)
        self.mainLayout.addWidget(self.progressBar, 2, 0, 1, 2)

        # box sizes
        self.controlGroupBox.setMinimumWidth(600)
        self.plot2.setMinimumWidth(800)
        self.plot2.setMinimumHeight(200)
        self.plot3.setMinimumWidth(800)
        self.plot3.setMinimumHeight(200)
        self.setLayout(self.mainLayout)
        self.setWindowTitle("SPAD Probe Acquisition")

        # set plot axes
        self.setPlotWidget(self.plot1, 0, 512, 0, 512, 'Pixel', 'Counts', '', '')
        self.setPlotWidget(self.plot2, 0, 512, 0, 1, 'Pixel', 'Accumulated Counts', '', '')
        self.setPlotWidget(self.plot3, 0, 512, 0, 63, 'Pixel', 'Flattened Counts', '', '')

        self.getValuesFromGUI()

        print('GUI initialized.')

    def getValuesFromGUI(self):
        # Acquisition settings
        self.Flash = int(self.tglFlash.isChecked())
        self.Reset = int(self.tglReset.isChecked())
        self.ReprogPLL = int(self.tglReprogPLL.isChecked())
        self.Parse = int(self.tglParse.isChecked())
        self.Save = int(self.tglSave.isChecked())
        # parameters
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
        # self.sidx = self.LEsidx.text()  # throws error when 'Run' is clicked

        self.clkdiv = round(int(self.fvco) / int(self.frep))

    @pyqtSlot()
    def ifbtnFlashClicked(self):
        self.getValuesFromGUI()
        flash = True
        reset = True
        reprogpll = True
        parseenable = False
        saveenable = False
        getdata = False

        [self.img, self.scatt, self.goodframes] = acquire_bytearray_extinput.AcqOK(flash, reset, reprogpll, parseenable,
            saveenable, getdata, self.npix, self.bitfile, self.rstcode, self.fpgaSwitches, self.clkdiv, self.duty,
            self.phase, self.flen, self.fignore, self.fnum, self.inum, self.sdir, self.sname).outputdata()

    @pyqtSlot()
    def ifbtnResetClicked(self):
        self.getValuesFromGUI()
        flash = False
        reset = True
        reprogpll = True
        parseenable = False
        saveenable = False
        getdata = False

        [self.img, self.scatt, self.goodframes] = acquire_bytearray_extinput.AcqOK(flash, reset, reprogpll, parseenable,
            saveenable, getdata, self.npix, self.bitfile, self.rstcode, self.fpgaSwitches, self.clkdiv, self.duty,
            self.phase, self.flen, self.fignore, self.fnum, self.inum, self.sdir, self.sname).outputdata()

    @pyqtSlot()
    def ifbtnRunClicked(self):
        self.startMainThread()
        self.startSideThread()

    @pyqtSlot()
    def ifbtnStopClicked(self):
        self.stopMainThread()
        print('mainthreadtimer stopped')
        self.stopSideThread()
        print('sidethread stopped')

    def createControlGroupBox(self):
        self.controlGroupBox = QGroupBox("Controls")

        # create and initialize lineEdits
        self.LEbitfile = QLineEdit('bitfile\\Nov2018_dualprobe_v1_03mmfpc_pll_intclk.bit')
        self.LErstcode = QLineEdit('7')
        self.LEswitch = QLineEdit('10000000100110000')
        self.LEfvco = QLineEdit('960')
        self.LEfrep = QLineEdit('10')
        self.LEduty = QLineEdit('50')
        self.LEphase = QLineEdit('180')
        self.LEflen = QLineEdit('1000')
        self.LEfignore = QLineEdit('10')
        self.LEfnum = QLineEdit('1000')
        self.LEinum = QLineEdit('100')  # or infinite
        self.LEtacq = QLineEdit('?')
        self.LEsdir = QLineEdit('rawdata')
        self.LEsname = QLineEdit('sample')
        self.LEsidx = QLineEdit('1')

        # create text labels
        Tbitfile = QLabel('Bitfile');         Tbitfile.setBuddy(self.LEbitfile)
        Trstcode = QLabel('Rst Code');         Trstcode.setBuddy(self.LErstcode)
        Tswitch = QLabel('FPGA Switches');         Tswitch.setBuddy(self.LEswitch)
        Tclock = QLabel('Clock')
        Tfvco = QLabel('Fvco');         Tfvco.setBuddy(self.LEfvco)
        Tfrep = QLabel('Rep Rate');         Tfrep.setBuddy(self.LEfrep)
        Tduty = QLabel('Duty Cycle');         Tduty.setBuddy(self.LEduty)
        Tphase = QLabel('Phase');         Tphase.setBuddy(self.LEphase)
        Tacquire = QLabel('Acquire')
        Tflen = QLabel('Frame length');         Tflen.setBuddy(self.LEflen)
        Tfignore = QLabel('Pass length');         Tfignore.setBuddy(self.LEfignore)
        Tfnum = QLabel('#Frames');         Tfnum.setBuddy(self.LEfnum)
        Tinum = QLabel('#Images');         Tinum.setBuddy(self.LEinum)
        Ttacq = QLabel('Tacq/Img');         Ttacq.setBuddy(self.LEtacq)
        Tsave = QLabel('Save')
        Tsdir = QLabel('Dir');         Tsdir.setBuddy(self.LEsdir)
        Tsname = QLabel('Name');         Tsname.setBuddy(self.LEsname)
        Tsidx = QLabel('Nxt Idx');         Tsidx.setBuddy(self.LEsidx)

        # create buttons
        self.btnFlash = QPushButton("Flash");         self.btnFlash.setDefault(True)
        self.btnReset = QPushButton("Reset");         self.btnReset.setDefault(True)
        btngroup1 = QButtonGroup(self.controlGroupBox);         btngroup1.setExclusive(False)
        self.tglFlash = QRadioButton("Flash");         self.tglFlash.setChecked(False)
        self.tglReset = QRadioButton("Reset");         self.tglReset.setChecked(True)
        self.tglReprogPLL = QRadioButton("reprogram PLL");         self.tglReprogPLL.setChecked(False)
        self.tglParse = QRadioButton("Parse");         self.tglParse.setChecked(False)
        self.tglSave = QRadioButton("Save");         self.tglSave.setChecked(True)
        btngroup1.addButton(self.tglFlash)
        btngroup1.addButton(self.tglReset)
        btngroup1.addButton(self.tglReprogPLL)
        btngroup1.addButton(self.tglParse)
        btngroup1.addButton(self.tglSave)
        self.btnRun = QPushButton("Run");         self.btnRun.setDefault(False)
        self.btnStop = QPushButton("Stop");         self.btnStop.setDefault(False)

        # create layout
        boxlayout = QVBoxLayout()

        line = [Tbitfile, self.LEbitfile, self.btnFlash]
        size = [1, 100, 1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Trstcode, self.LErstcode, Tswitch, self.LEswitch, self.btnReset]
        size = [1, 1, 1, 80, 1, 1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Tclock, Tfvco, self.LEfvco, Tfrep, self.LEfrep, Tduty, self.LEduty, Tphase, self.LEphase]
        size = [1, 0, 1, 0, 1, 0, 1, 0, 1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Tacquire, Tflen, self.LEflen, Tfignore, self.LEfignore, Tfnum, self.LEfnum, Tinum, self.LEinum, Ttacq,
                self.LEtacq]
        size = [2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Tsave, Tsdir, self.LEsdir, Tsname, self.LEsname, Tsidx, self.LEsidx]
        size = [2, 1, 100, 1, 30, 1, 1]
        self.layoutSingleLine(boxlayout, line, size)
        line = [self.tglFlash, self.tglReset, self.tglReprogPLL, self.tglParse, self.tglSave, self.btnRun, self.btnStop]
        size = [1, 1, 1, 1, 1, 100, 100]
        self.layoutSingleLine(boxlayout, line, size)

        self.controlGroupBox.setLayout(boxlayout)

    def setPlotWidget(self, plot, xmin, xmax, ymin, ymax, xlabel, ylabel, xunit, yunit):
        plot.setLabel('bottom', xlabel, units=xunit)
        plot.setLabel('left', ylabel, units=yunit)
        plot.setXRange(xmin, xmax)
        plot.setYRange(ymin, ymax)

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

    def advanceProgressBar(self):
        curVal = self.progressBar.value()
        maxVal = self.progressBar.maximum()
        self.progressBar.setValue(curVal + int((maxVal - curVal) / 100))


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName('SPADProbeAcquire')
    app.setStyle("fusion")
    main = WidgetGallery()
    main.resize(1200, 600)
    main.show()
    sys.exit(app.exec_())
