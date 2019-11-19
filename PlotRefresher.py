import threading
import Constants

constants = Constants.Instance()


class PlotRefresher(object):

    def __init__(self):
        self.plot1Handle = None
        self.plot2Handle = None
        self.plot1Number = 0
        self.plot2Number = 2
        self.plot1YLim = [0, 0]
        self.plot2YLim = [0, 0]

        # Plot refresher thread control
        self.plotRefresherThread = threading.Thread(target=self.plotRefresher)
        self.stopPlotRefresher = threading.Event()

        # Initialize a maximum of 8 channel's data
        self.channels = [None] * 2

        self.channelLock = threading.RLock()

        # Initialize the down sample counter
        self.dispDownsampleCounter = [0] * 8
        self.saveDownsampleCounter = [0] * 8

    def updatePlots(self):
        self.channelLock.acquire()

        if not self.channels[self.plot1Number].isEmpty():
            self.plot1Handle.clear()
            self.plot1Handle.plot(self.channels[self.plot1Number].getData())
            self.plot1Handle.setXRange(0, 512)

        if not self.channels[self.plot2Number].isEmpty():
            self.plot2Handle.clear()
            self.plot2Handle.plot(self.channels[self.plot2Number].getData())
            self.plot2Handle.setXRange(0, 512)
            self.plot2Handle.getAxis('bottom').setLabel('Time', units='s')

        self.channelLock.release()


    def plotRefresher(self):
        while not self.stopPlotRefresher.wait(constants.PLOT_REFRESHING_INTERVAL):
            self.channelLock.acquire()
            data = 1  # replace
            if data != None:
                adcRange = fpga.getADCRefValue()

                for i in range(data.getSize()):
                    point = data[i]
                    addr = int(point / 4096)
                    value = float(point % 4096) / constants.DAC_MAX_CODE * adcRange
                    if addr >= 8:
                        pass
                    else:
                        self.dispDownsampleCounter[addr] = self.dispDownsampleCounter[addr] + 1
                        if self.dispDownsampleCounter[addr] == constants.DATA_DISP_DOWNSAMPLE:
                            self.dispDownsampleCounter[addr] = 0
                            self.channels[addr].push(value)
            self.channelLock.release()

    def startPlotRefresherThread(self):
        if not self.plotRefresherThread.isAlive():
            self.plotRefresherThread = threading.Thread(target=self.plotRefresher)

        try:
            self.plotRefresherThread.start()
        except RuntimeError as e:
            a = 1
        else:
            self.stopPlotRefresher.clear()

    def stopPlotRefresherThread(self):
        self.stopPlotRefresher.set()
