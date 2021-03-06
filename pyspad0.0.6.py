import glob

print('python code starting')

import os
import threading
import time
# pg.setConfigOption('background', 'w')
from pathlib import Path
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QRadioButton, QVBoxLayout, QButtonGroup, QProgressBar, QMessageBox)
import Constants
import itsallok
import parse_singledat2

fpga = itsallok.Instance()
constants = Constants.Instance()


class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        # global parameters upon initiation
        self.sidx = 0
        self.curipublic = 0
        self.lastdeleted = 0
        self.deletebuffer = 1
        self.npix = 512


        # declare locks
        self.datalock = threading.RLock()  # only blocks if the lock is held by ANOTHER thread

        # initialize GUI
        self.initializeGUI()
        self.createDirs()  # create dirs

        # connect buttons
        self.btnRun.clicked.connect(self.ifbtnRunClicked)
        self.btnFlash.clicked.connect(self.ifbtnFlashClicked)
        self.btnReset.clicked.connect(self.ifbtnResetClicked)
        self.btnStop.clicked.connect(self.ifbtnStopClicked)

        # empty data
        self.img = np.zeros(self.npix, dtype=np.uint64)
        self.scatt = np.zeros(self.fnum * self.npix, dtype=np.uint8)
        self.goodframes = 0

        # Connect ot hardware (Opal Kelly XEM3010)
        self.connectFPGA()



        # create sidethread : search recent and plot thread
        self.sidethreadinstance = threading.Thread(target=self.sideThread)
        self.stopsidethreadflag = threading.Event()
        self.startSideThread()
        self.sideThreadON = False

        # create acqthread : data acquisition thread
        self.acqthreadinstance = threading.Thread(target=self.acqThread)
        self.stopacqthreadflag = threading.Event()
        self.startAcqThread()
        self.acqThreadON = False

        # add to main thread timer
        self.mainThreadTimer = QTimer(self)
        self.startMainThread()

    ## OPAL KELLY ######################################################################################################

    def connectFPGA(self):

        fpga.OpenBySerial(fpga.GetDeviceListSerial(0))
        print("Connecting Opal Kelly device ...")
        if fpga.IsOpen():
            print("Successfully connected to Opal Kelly.")
        else:
            print("Connection failed.")

    def flashFPGA(self):
        fpga.flash(self.bitfile)

    def resetFPGA(self):
        fpga.reset(self.rstcode)

    def repllFPGA(self):
        fpga.reprogPLL(self.flen, self.clkdiv, self.phase, self.duty, self.fpgaSwitches)

    ## THREADING #######################################################################################################

    # acqThread: find most recent file and parse it.
    def acqThread(self):
        while not self.stopacqthreadflag.wait(constants.PLOT_REFRESHING_INTERVAL):
            if self.acqThreadON:
                print('run acqThread')
                self.getValuesFromGUI()
                self.inputValuesToGUI()

                ts0 = time.time()
                timestamp = np.zeros(self.inum)
                self.curi = 0
                while (self.curi < self.inum) & self.acqThreadON:  # (not self.stopacqthreadflag.is_set()):
                    # print(threading.current_thread().ident)
                    [data_out, ts] = fpga.acquireDataSingle(self.fnum, self.fignore, self.fpgaSwitches)
                    timestamp[self.curi] = ts - ts0
                    self.datalock.acquire()
                    with open(self.sdir + '\\' + self.sname + '_raw' + str(self.sidx).zfill(3) + '_i' + str(self.curi).zfill(4), 'wb') as f:
                        f.write(data_out)
                    self.datalock.release()
                    dT = (timestamp[self.curi] - timestamp[max(0, self.curi-1)]) * 1000
                    print('     Image %i Timestamp = %.3f s, dT = %.2f ms' % (self.curi, timestamp[self.curi], dT))

                    self.datalock.acquire()
                    self.curipublic = self.curi
                    self.datalock.release()

                    self.curi = self.curi + 1

                with open(self.tsdir + '\\' + self.sname + '_timestamp' + str(self.sidx).zfill(3), 'wb') as f:
                    f.write(bytes(timestamp))

                print('stopped acqThread')
                self.acqThreadON = False
                self.sideThreadON = False

    def startAcqThread(self):
        # print(threading.current_thread().ident)
        # create acqthread if it doesn't exist already
        if not self.acqthreadinstance.isAlive():
            print('creating acqthread')
            self.acqthreadinstance = threading.Thread(target=self.acqThread)
            self.stopacqthreadflag.clear()
        else:
            print('acqthread has already been created')
            return

        # run acqthread instance after creating it
        try:
            print('starting acqthread')
            self.acqthreadinstance.start()  # should only be run once
        except RuntimeError as e:
            print('acqthread is already running')
        else:
            self.stopacqthreadflag.clear()

    def stopAcqThread(self):
        self.stopacqthreadflag.set()

    # sideThread: find most recent file and parse it.
    def sideThread(self):
        while not self.stopsidethreadflag.wait(constants.PLOT_REFRESHING_INTERVAL):  # this starts once and always runs until end
            prevfile = []
            # newest = None
            while self.sideThreadON:  # not self.stopsidethreadflag.is_set():
                # newest = self.getLatestFile()
                newest = self.sdir + '\\' + \
                         self.sname + '_raw' + str(self.sidx).zfill(3) +'_i' + str(self.curipublic).zfill(4)

                if os.path.exists(newest):  # if there is such a file
                    if (prevfile[-2:] != newest[-2:]):  # if file has been updated, parse and plot.
                        prevfile = newest
                        # print('file is new, so parse')

                        self.datalock.acquire()
                        # Parse the bytearray file
                        [self.img, self.scatt, self.goodframes] =\
                            parse_singledat2.Parse(self.npix, self.fnum, self.fignore, newest).get_data()
                        self.datalock.release()
                    # else:  # if file has not been updated, stop side thread.
                    #     self.sideThreadON = False
                    #     print('data no longer new')

                    if not self.ensave:  # if save switch is off, delete all recent files
                        if self.lastdeleted < self.curipublic - self.deletebuffer:
                            for filename in glob.glob(self.sdir + '\\' + self.sname + '_raw' + str(self.sidx).zfill(3) + '_i*'):
                                currentindex = int(filename[-3:])
                                # print('deleting everything before: ' + str(self.curipublic - self.deletebuffer))
                                if currentindex < self.curipublic - self.deletebuffer:
                                    try:
                                        # print('delete', filename)
                                        os.remove(filename)
                                    except OSError as e:
                                        # print('error')
                                        time.sleep(0.1)
                                    # print('deleted file: ' + filename)
                            self.lastdeleted = self.lastdeleted + self.deletebuffer

    def getLatestFile(self):  # no longer used, because index of it is known
        pathnow = Path(os.getcwd()) / self.sdir
        files = os.listdir(str(pathnow))
        for i in range(0, len(files)):
            files[i] = str(pathnow / files[i])
        files = sorted(files, key=os.path.getmtime, reverse=True)
        newest = files[0]
        return newest

    def startSideThread(self):
        # create sidethread if it doesn't exist already
        if not self.sidethreadinstance.isAlive():
            print('creating sidethread')
            self.sidethreadinstance = threading.Thread(target=self.sideThread)
            self.stopsidethreadflag.clear()
        else:
            print('sidethread has already been created')
            return

        # run sidethread instance after creating it
        try:
            print('starting sidethread')
            self.sidethreadinstance.start()
        except RuntimeError as e:
            print('sidethread is already running')
        else:
            self.stopsidethreadflag.clear()

    def stopSideThread(self):  # only called when application is closed.
        self.stopsidethreadflag.set()

    # main thread
    def mainThread(self):
        if self.enplot & self.sideThreadON:
            self.updatePlots()  # must be in main thread.

    def updatePlots(self):
        self.plot2.clear()
        self.plot3.clear()

        self.datalock.acquire()
        self.plot2.plot(self.img)  # flattened image
        self.plot3.plot(np.tile(range(0, self.npix), self.goodframes), self.scatt[0:self.goodframes * self.npix])
        # self.plot3.setData(self.scatt[0:self.goodframes * self.npix])

        # self.setPlotWidget(self.plot2, 0, 512, 0, max(self.img), 'Pixel', 'Accumulated Counts', '', '')  # might have to revive for scaling
        # self.setPlotWidget(self.plot3, 0, 512, 0, max(self.scatt), 'Pixel', 'Flattened Counts', '', '')
        self.datalock.release()
        # print('plot was updated')

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
        time.sleep(1)
        event.accept()

    #########################################################################################################

    def createDirs(self):
        if not os.path.exists(self.sdir):
            os.mkdir(self.sdir)

        if not os.path.exists(self.tsdir):
            os.mkdir(self.tsdir)


    def initializeGUI(self):
        # create widgets
        self.originalPalette = QApplication.palette()
        self.createControlGroupBox()

        self.getValuesFromGUI()
        self.inputValuesToGUI()
        self.createProgressBar()

        # create plots
        self.plot1 = pg.PlotWidget(name='Plot1')
        self.plot2 = pg.PlotWidget(name='Plot2')
        self.plot3 = pg.PlotWidget(name='Plot3')

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

        print('GUI initialized.')

    def getValuesFromGUI(self):
        self.datalock.acquire()
        # Acquisition settings
        self.ensave = self.tglSave.isChecked()
        self.enplot = self.tglPlot.isChecked()

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
        self.datalock.release()

    def inputValuesToGUI(self):
        self.datalock.acquire()
        self.tacq = (self.flen)*self.fnum*(self.duty/100)/(self.frep*1000000)  # acquisition time per image (sec)
        self.clkdiv = round(int(self.fvco) / int(self.frep))

        self.LEtacq.setText(str(self.tacq))
        self.LEsidx.setText(str(self.sidx))
        self.datalock.release()

    @pyqtSlot()
    def ifbtnFlashClicked(self):
        self.getValuesFromGUI()
        self.inputValuesToGUI()
        self.flashFPGA()


    @pyqtSlot()
    def ifbtnResetClicked(self):
        self.getValuesFromGUI()
        self.inputValuesToGUI()
        self.curipublic = 0
        self.lastdeleted = self.deletebuffer
        self.resetFPGA()
        self.repllFPGA()

    @pyqtSlot()
    def ifbtnRunClicked(self):
        print('Run clicked')
        self.getValuesFromGUI()
        self.sidx = self.sidx + 1
        self.inputValuesToGUI()
        self.curipublic = 0
        self.lastdeleted = self.deletebuffer
        self.progressBar.setRange(0, self.inum - 1)
        self.progressBar.setValue(0)

        self.resetFPGA()
        self.repllFPGA()  # without this, some values from GUI are not applied to the FSM.
        # self.startAcqThread()
        # time.sleep(0.1)
        # self.startSideThread()
        self.acqThreadON = True
        self.sideThreadON = True

    @pyqtSlot()
    def ifbtnStopClicked(self):
        # self.stopAcqThread()
        # self.stopSideThread()
        # self.stopMainThread()
        self.enplot = False
        self.acqThreadON = False
        self.sideThreadON = False
        print('Stop clicked')

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
        self.btnRun = QPushButton("Run");         self.btnRun.setDefault(False)
        self.btnStop = QPushButton("Stop");         self.btnStop.setDefault(False)
        self.tglSave = QRadioButton("Save data");         self.tglSave.setChecked(True)
        self.tglPlot = QRadioButton("Live Plotting");         self.tglPlot.setChecked(True)
        btngroup1 = QButtonGroup(self.controlGroupBox); btngroup1.setExclusive(False)
        btngroup2 = QButtonGroup(self.controlGroupBox); btngroup2.setExclusive(False)
        btngroup1.addButton(self.tglSave)
        btngroup2.addButton(self.tglPlot)

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
        line = [self.tglSave, self.tglPlot, self.btnRun, self.btnStop]
        size = [1, 1, 2, 2]
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

    def createProgressBar(self):
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, self.inum - 1)
        self.progressBar.setValue(0)

        timer = QTimer(self)
        timer.timeout.connect(self.advanceProgressBar)
        timer.start(constants.PLOT_REFRESHING_INTERVAL * 1000)

    def advanceProgressBar(self):
        # curVal = self.progressBar.value()
        curVal = self.curipublic
        maxVal = self.progressBar.maximum()
        self.progressBar.setValue(curVal + int((maxVal - curVal) / 100))




if __name__ == '__main__':
    import sys
    print('Initializing application')

    app = QApplication(sys.argv)
    app.setApplicationName('SPADProbeAcquire')
    app.setStyle("fusion")
    main = WidgetGallery()
    print('Creating WidgetGallery')
    main.resize(1200, 600)
    main.show()
    sys.exit(app.exec_())
