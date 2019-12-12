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
from pathlib import Path
import Constants
import os

import acquire_bytearray_extflag
import acquireandsave
import parse_singledat
import signal
import manageok

constants = Constants.Instance()


class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        # global parameters upon initiation
        self.sidx = 0
        self.npix = 512

        # initialize GUI
        self.initializeGUI()
        self.getValuesFromGUI()
        self.inputValuesToGUI()

        # connect buttons
        self.btnRun.clicked.connect(self.ifbtnRunClicked)
        self.btnFlash.clicked.connect(self.ifbtnFlashClicked)
        self.btnReset.clicked.connect(self.ifbtnResetClicked)
        self.btnStop.clicked.connect(self.ifbtnStopClicked)

        # empty data
        self.img = np.zeros(self.npix, dtype=np.uint64)
        self.scatt = np.zeros(self.fnum * self.npix, dtype=np.uint8)
        self.goodframes = 0

        # declare locks
        self.datalock = threading.RLock()  # only blocks if the lock is held by ANOTHER thread

        # create sidethread
        self.sidethreadinstance = threading.Thread(target=self.sideThread)
        self.stopsidethreadflag = threading.Event()

        # create acqthread
        self.acqthreadinstance = threading.Thread(target=self.acqThread)
        self.stopacqthreadflag = threading.Event()

        # add to main thread timer
        self.mainThreadTimer = QTimer(self)

        signal.signal(signal.SIGINT, self.signal_handler)

    ## THREADING #######################################################################################################

    def signal_handler(signal):
        global interrupted
        interrupted = True

    # acqThread: find most recent file and parse it.
    def acqThread(self):
        print('run acqThread')

        self.getValuesFromGUI()
        self.inputValuesToGUI()

        enflash = True
        enreset = True
        enreprogpll = True
        interrupted = False

        manageok.ManageOK(enflash, enreset, enreprogpll, interrupted,
            self.npix, self.bitfile, self.rstcode, self.fpgaSwitches, self.clkdiv, self.duty, self.phase,
            self.flen, self.fignore, self.fnum, self.inum, self.sdir, self.sname + str(self.sidx).zfill(4), self.tsdir)

        print('stopped acqThread')

    def startAcqThread(self):
        # create acqthread if it doesn't exist already
        if not self.acqthreadinstance.isAlive():
            print('creating acqthread')
            self.acqthreadinstance = threading.Thread(target=self.acqThread)
            self.stopacqthreadflag.clear()
        else:
            print('acqthread has already been created')

        # run acqthread instance after creating it
        try:
            self.acqthreadinstance.start()
        except RuntimeError as e:
            print('acqthread is already running')
        else:
            self.stopacqthreadflag.clear()

    def stopAcqThread(self):
        self.stopacqthreadflag.set()

    # sideThread: find most recent file and parse it.
    def sideThread(self):
        print('run sideThread')

        while not self.stopsidethreadflag.is_set():
            newest = self.getLatestFile()
            # self.datalock.acquire()

            [self.img, self.scatt, self.goodframes] =\
                parse_singledat.Parse(self.npix, self.fnum, self.fignore, newest).get_data()

            # self.datalock.release()

        print('stopped sideThread')

    def getLatestFile(self):
        pathnow = Path(os.getcwd()) / self.sdir
        files = os.listdir(str(pathnow))
        for i in range(0, len(files)):
            files[i] = str(pathnow / files[i])
        files = sorted(files, key=os.path.getmtime, reverse=True)
        newest = files[0]
        print('newest file is: ' + newest)
        return newest

    def startSideThread(self):
        # create sidethread if it doesn't exist already
        if not self.sidethreadinstance.isAlive():
            print('creating sidethread')
            self.sidethreadinstance = threading.Thread(target=self.sideThread)
            self.stopsidethreadflag.clear()
        else:
            print('sidethread has already been created')

        # run sidethread instance after creating it
        try:
            self.sidethreadinstance.start()
        except RuntimeError as e:
            print('sidethread is already running')
        else:
            self.stopsidethreadflag.clear()

    def stopSideThread(self):
        self.stopsidethreadflag.set()

    # main thread
    def mainThread(self):
        self.updatePlots()

    def updatePlots(self):
        # self.datalock.acquire()
        self.plot2.clear()
        self.plot3.clear()

        self.plot2.plot(self.img)  # flattened image
        self.plot3.plot(np.tile(range(0, self.npix), self.goodframes), self.scatt[0:self.goodframes * self.npix])

        self.setPlotWidget(self.plot2, 0, 512, 0, max(self.img), 'Pixel', 'Accumulated Counts', '', '')
        # self.setPlotWidget(self.plot3, 0, 512, 0, max(self.scatt), 'Pixel', 'Flattened Counts', '', '')
        # self.datalock.release()
        print('plot was updated')

    def startMainThread(self):
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
        self.stopSideThread()
        self.stopAcqThread()
        self.stopMainThread()
        # Wait for the opal kelly components to clean itself properly
        # Otherwise core dump is likely to be raised
        time.sleep(0.5)
        event.accept()

    #########################################################################################################

    def initializeGUI(self):
        # create widgets
        self.originalPalette = QApplication.palette()
        self.createControlGroupBox()
        # self.createProgressBar()
        self.plot1 = pg.PlotWidget(name='Plot1')
        self.plot2 = pg.PlotWidget(name='Plot2')
        self.plot3 = pg.PlotWidget(name='Plot3')

        # place different widgets on mainLayout
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.controlGroupBox, 0, 0)
        self.mainLayout.addWidget(self.plot1, 1, 0)
        self.mainLayout.addWidget(self.plot2, 0, 1)
        self.mainLayout.addWidget(self.plot3, 1, 1)
        # self.mainLayout.addWidget(self.progressBar, 2, 0, 1, 2)

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
        self.inputValuesToGUI()

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
        self.fvco = int(self.LEfvco.text())
        self.frep = int(self.LEfrep.text())
        self.duty = int(self.LEduty.text())
        self.phase = int(self.LEphase.text())
        self.flen = int(self.LEflen.text())  # ep02wire. framelength
        self.fignore = int(self.LEfignore.text())
        self.fnum = int(self.LEfnum.text())  # number of frames, a.k.a. datasize
        self.inum = int(self.LEinum.text())  # number of images
        self.sdir = self.LEsdir.text()  # directory where data are saved
        self.sname = self.LEsname.text()
        self.tsdir = 'timestamp'  # directory where timestamps are saved

    def inputValuesToGUI(self):
        self.tacq = (self.flen)*self.fnum*(self.duty/100)/(self.frep*1000000)  # acquisition time per image (sec)
        self.clkdiv = round(int(self.fvco) / int(self.frep))

        self.LEtacq.setText(str(self.tacq))
        self.LEsidx.setText(str(self.sidx))

    @pyqtSlot()
    def ifbtnFlashClicked(self):
        self.getValuesFromGUI()
        self.inputValuesToGUI()
        enflash = True
        enreset = True
        enreprogpll = True


    @pyqtSlot()
    def ifbtnResetClicked(self):
        self.getValuesFromGUI()
        self.inputValuesToGUI()
        enflash = False
        enreset = True
        enreprogpll = True



    @pyqtSlot()
    def ifbtnRunClicked(self):
        self.getValuesFromGUI()
        self.sidx = self.sidx + 1
        self.inputValuesToGUI()
        self.startAcqThread()
        time.sleep(1)
        self.startSideThread()
        self.startMainThread()

    @pyqtSlot()
    def ifbtnStopClicked(self):
        self.stopAcqThread()
        self.stopSideThread()
        self.stopMainThread()
        interrupted = True

    def createControlGroupBox(self):
        self.controlGroupBox = QGroupBox("Controls")

        # create and initialize lineEdits
        self.createLineEditsAndInit()

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
        Tflen = QLabel('LenFr');         Tflen.setBuddy(self.LEflen)
        Tfignore = QLabel('LenIg');         Tfignore.setBuddy(self.LEfignore)
        Tfnum = QLabel('#Fr');         Tfnum.setBuddy(self.LEfnum)
        Tinum = QLabel('#Im');         Tinum.setBuddy(self.LEinum)
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
        size = [2, 1, 2, 1, 1, 1, 2, 1, 2, 1, 2]
        self.layoutSingleLine(boxlayout, line, size)
        line = [Tsave, Tsdir, self.LEsdir, Tsname, self.LEsname, Tsidx, self.LEsidx]
        size = [2, 1, 30, 1, 30, 1, 10]
        self.layoutSingleLine(boxlayout, line, size)
        line = [self.tglFlash, self.tglReset, self.tglReprogPLL, self.tglParse, self.tglSave, self.btnRun, self.btnStop]
        size = [1, 1, 1, 1, 1, 100, 100]
        self.layoutSingleLine(boxlayout, line, size)

        self.controlGroupBox.setLayout(boxlayout)

    def createLineEditsAndInit(self):
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
        self.LEinum = QLineEdit('20')  # or infinite
        self.LEtacq = QLineEdit('-')
        self.LEsdir = QLineEdit('rawdata')
        self.LEsname = QLineEdit('sample')
        self.LEsidx = QLineEdit('0')

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

    # def createProgressBar(self):
    #     self.progressBar = QProgressBar()
    #     self.progressBar.setRange(0, 10000)
    #     self.progressBar.setValue(0)
    #
    #     timer = QTimer(self)
    #     timer.timeout.connect(self.advanceProgressBar)
    #     timer.start(1000)

    # def advanceProgressBar(self):
    #     curVal = self.progressBar.value()
    #     maxVal = self.progressBar.maximum()
    #     self.progressBar.setValue(curVal + int((maxVal - curVal) / 100))


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName('SPADProbeAcquire')
    app.setStyle("fusion")
    main = WidgetGallery()
    main.resize(1200, 600)
    main.show()
    sys.exit(app.exec_())
