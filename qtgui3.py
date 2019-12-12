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


class ThRunAcq(QThread):
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        main.getValuesFromGUI()
        getdata = True

        acquire_bytearray_nooutput.AcqOK(
            main.Flash, main.Reset, main.ReprogPLL, main.Parse, main.Save, getdata,
            main.npix, main.bitfile, main.rstcode, main.fpgaSwitches, main.clkdiv, main.duty, main.phase,
            main.flen, main.fignore, main.fnum, main.inum, main.sdir, main.sname + str(main.sidx).zfill(4))


# class PlotLive(object):  # find most recent, parse it, and update
#     def __init__(self):
#         print('a')
#         self.plot()
#
#     def get_latest_file(self):
#         print('c')
#         print(main.sdir)
#         pathnow = os.getcwd() + '\\' + main.sdir + '\\'
#         files = os.listdir(pathnow)
#         for i in range(0, len(files)):
#             files[i] = pathnow + files[i]
#         files2 = sorted(files, key=os.path.getmtime)
#         newest = files2[-1]
#         return newest
#
#     def plot(self):
#         print('b')
#         newest = self.get_latest_file()
#         print(newest)
#         [main.img, main.scatt, main.goodframes] = \
#             parse_singledat.Parse(main.npix, main.fnum, main.fignore, newest).get_data()
#
#         # update plots with parsed data
#         main.plot2.plot(main.img)  # flattened image
#         main.plot3.plot(np.tile(range(0, main.npix), main.goodframes),
#                         main.scatt[0:main.goodframes * main.npix])  # raw count scatterplot
#         main.setPlotWidget(main.plot2, 0, 512, 0, max(main.img), 'Pixel', 'Accumulated Counts', '', '')
#         main.setPlotWidget(main.plot3, 0, 512, 0, max(main.scatt), 'Pixel', 'Flattened Counts', '', '')


# class Worker(QObject):
#     stepIncreased = Signal(int)
#
#     def __init__(self):
#         super(Worker, self).__init__()
#         self._step = 0
#         self._isRunning = True
#         self._maxSteps = 20
#
#     def get_latest_file(self):
#         pathnow = os.getcwd() + '\\' + main.sdir  + '\\'
#         files = os.listdir(pathnow)
#         for i in range(0, len(files)):
#             files[i] = pathnow + files[i]
#         files2 = sorted(files, key=os.path.getmtime)
#         newest = files2[-1]
#         return newest
#
#     def task(self):
#         if not self._isRunning:
#             self._isRunning = True
#             self._step = 0
#
#         while main.threadplotOn:
#             # time.sleep(0.5)
#             newest = self.get_latest_file()
#             print(newest)
#             [main.img, main.scatt, main.goodframes] = \
#                 parse_singledat.Parse(main.npix, main.fnum, main.fignore, newest).get_data()
#
#             # update plots with parsed data
#             # main.plot2.plot(main.img)  # flattened image
#             # main.plot3.plot(np.tile(range(0, main.npix), main.goodframes),
#             #                 main.scatt[0:main.goodframes * main.npix])  # raw count scatterplot
#             # main.setPlotWidget(main.plot2, 0, 512, 0, max(main.img), 'Pixel', 'Accumulated Counts', '', '')
#             # main.setPlotWidget(main.plot3, 0, 512, 0, max(main.scatt), 'Pixel', 'Flattened Counts', '', '')
#
#         print "finished..."
#
#     def stop(self):
#         self._isRunning = False


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

        # create threads
        self.threadrun = ThRunAcq()
        # self.threadplot = ThPlotLive()
        # self.threadplotOn = True

        # threads, from Yihan's
        # self.plotRefresherThread = threading.Thread()  # 'target' statement deleted
        # self.stopPlotRefresher = threading.Event()
        # self.channelLock = threading.RLock()

        self.mainThreadTimer = QTimer(self)
        self.startMainThread()

    ####################################################################################################################

    def startMainThread(self):
        if self.mainThreadTimer.isActive():
            self.mainThreadTimer.stop()
        self.mainThreadTimer.timeout.connect(self.mainThread)
        self.mainThreadTimer.setInterval(constants.MAIN_UPDATING_INTERVAL)
        self.mainThreadTimer.setSingleShot(False)
        self.mainThreadTimer.start()

    def mainThread(self):
        self.plotlive()

    def plotlive(self):  # find most recent, parse it, and update
        newest = self.get_latest_file()
        [self.img, self.scatt, self.goodframes] = \
            parse_singledat.Parse(self.npix, self.fnum, self.fignore, newest).get_data()

        # update plots with parsed data
        self.plot2.plot(self.img)  # flattened image
        self.plot3.plot(np.tile(range(0, self.npix), self.goodframes),
                        self.scatt[0:self.goodframes * self.npix])  # raw count scatterplot
        self.setPlotWidget(self.plot2, 0, 512, 0, max(self.img), 'Pixel', 'Accumulated Counts', '', '')
        self.setPlotWidget(self.plot3, 0, 512, 0, max(self.scatt), 'Pixel', 'Flattened Counts', '', '')

    def get_latest_file(self):
        pathnow = os.getcwd() + '\\' + self.sdir + '\\'
        files = os.listdir(pathnow)
        for i in range(0, len(files)):
            files[i] = pathnow + files[i]
        files2 = sorted(files, key=os.path.getmtime)
        newest = files2[-1]
        return newest

    # def stopMainThread(self):
    #     self.mainThreadTimer.stop()
    #
    # def closeEvent(self, event):
    #     print("Killing auto-updating threads ...")
    #     self.stopPlotRefresherThread()
    #     self.stopMainThread()
    #     print("Closing the connection to the Opal Kelly ...")
    #     # Wait for the opal kelly components to clean itself properly
    #     # Otherwise core dump is likely to be raised
    #     time.sleep(1.1)
    #     event.accept()
    #
    # def startPlotRefresherThread(self):
    #     if not self.plotRefresherThread.isAlive():
    #         self.plotRefresherThread = threading.Thread()
    #
    #     try:
    #         self.plotRefresherThread.start()
    #     except RuntimeError as e:
    #         a = 1
    #     else:
    #         self.stopPlotRefresher.clear()
    #
    # def stopPlotRefresherThread(self):
    #     self.stopPlotRefresher.set()
    #
    # def updatePlots(self):
    #     self.channelLock.acquire()
    #
    #     if not self.channels[self.plot1Number].isEmpty():
    #         self.plot1Handle.clear()
    #         self.plot1Handle.plot(self.channels[self.plot1Number].getData())
    #         self.plot1Handle.setXRange(0, 512)
    #
    #     if not self.channels[self.plot2Number].isEmpty():
    #         self.plot2Handle.clear()
    #         self.plot2Handle.plot(self.channels[self.plot2Number].getData())
    #         self.plot2Handle.setXRange(0, 512)
    #         self.plot2Handle.getAxis('bottom').setLabel('Time', units='s')
    #
    #     self.channelLock.release()





    ####################################################################################################################

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
                                                                                   saveenable, getdata,
                                                                                   self.npix, self.bitfile,
                                                                                   self.rstcode, self.fpgaSwitches,
                                                                                   self.clkdiv, self.duty, self.phase,
                                                                                   self.flen, self.fignore, self.fnum,
                                                                                   self.inum, self.sdir,
                                                                                   self.sname).outputdata()

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
                                                                                   saveenable, getdata,
                                                                                   self.npix, self.bitfile,
                                                                                   self.rstcode, self.fpgaSwitches,
                                                                                   self.clkdiv, self.duty, self.phase,
                                                                                   self.flen, self.fignore, self.fnum,
                                                                                   self.inum, self.sdir,
                                                                                   self.sname).outputdata()

    @pyqtSlot()
    def ifbtnRunClicked(self):
        self.threadrun.start()
        # self.threadplotOn = True
        # self.threadplot.start()

    @pyqtSlot()
    def ifbtnStopClicked(self):
        self.threadrun.terminate()
        # self.threadplotOn = False
        # self.threadplot.terminate()

        # When stop button is clicked, opal kelly stops responding to commands. Error Code -8. Need to add part to
        # re-secure opal kelly connection after terminating the data acquisition thread.

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
