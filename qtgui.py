from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSlot
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget)
import pyqtgraph as pg
import numpy as np
#import matplotlib.pyplot as plt


# pg.setConfigOption('background', 'w')



class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        self.originalPalette = QApplication.palette()
        self.createControlGroupBox()
        self.createProgressBar()

        #declare plot widgets
        self.pw1 = pg.PlotWidget(name='Plot1')
        self.pw2 = pg.PlotWidget(name='Plot2')
        self.pw3 = pg.PlotWidget(name='Plot3')

        #place different widgets on the layout
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.controlGroupBox, 0, 0)
        mainLayout.addWidget(self.pw1, 1, 0)
        mainLayout.addWidget(self.pw2, 0, 1)
        mainLayout.addWidget(self.pw3, 1, 1)
        mainLayout.addWidget(self.progressBar, 2, 0, 1, 2)

        self.setLayout(mainLayout)
        self.setWindowTitle("SPAD Probe Acquisition")

        #set axes
        self.setPlotWidget(self.pw1, 0, 512, 0, 512, 'Pixel', 'Counts', '', '')

        #if button is clicked
        self.runButton.clicked.connect(self.ifButtonClicked)

    @pyqtSlot()
    def ifButtonClicked(self):
        import parse
        # inputBitfile = QLineEdit.text(self.lineEdit1)
        inputBitfile = self.lineEdit1.text()
        inputSavedir = self.lineEdit2.text()
        inputNframes = self.lineEdit3.text()

        #declare variables (will be integrated)
        npix=512
        datasize=1000
        ignoreframes=10
        # dir='D:\\dropbox\\Dropbox\\Projects\\SpadProbe\\git\\pyspad\\rawdata\\'
        # dir='D:\\dropbox\\Dropbox\\Projects\\SpadProbe\\201907_caltech5\\codepackage_aftertrip\\rawdata\\'
        dir='D:\\dropbox\\Dropbox\\Projects\\SpadProbe\\201902_caltechGcamp\\code package\\outfile\\0223\\0223_recording_LP57\\'
        iframe=4

        #fetch data from parse module
        [self.img, self.scatt, self.goodframes] = parse.Parse(npix, datasize, ignoreframes, inputSavedir, int(inputNframes)).get_data()

        #update plots with parsed data
        self.pw2.plot(self.img) #flattened image
        self.pw3.plot(np.tile(range(0,npix),self.goodframes), self.scatt[0:self.goodframes*npix]) #raw count scatterplot

        self.setPlotWidget(self.pw2, 0, 512, 0, max(self.img), 'Pixel', 'Accumulated Counts', '', '')
        self.setPlotWidget(self.pw3, 0, 512, 0, max(self.scatt), 'Pixel', 'Flattened Counts', '', '')

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

        radioButton1 = QRadioButton("Image Acquisition")
        radioButton2 = QRadioButton("Phase Sweep")
        radioButton1.setChecked(True)

        layoutOption = QHBoxLayout()
        layoutOption.addWidget(radioButton1)
        layoutOption.addWidget(radioButton2)

        self.lineEdit1 = QLineEdit(self)
        # lineEdit1 = QLineEdit('enter full path of bitfile')
        self.lineEdit2 = QLineEdit('D:\\dropbox\\Dropbox\\Projects\\SpadProbe\\201902_caltechGcamp\\code package\\outfile\\0223\\0223_recording_LP57\\')
        self.lineEdit3 = QLineEdit('4')

        titleOption = QLabel("Acq Option")
        title1 = QLabel('bitfile')
        title1.setBuddy(self.lineEdit1)
        title2 = QLabel('savedir')
        title2.setBuddy(self.lineEdit2)
        title3 = QLabel('#frames')
        title3.setBuddy(self.lineEdit3)

        self.runButton = QPushButton("Run")
        self.runButton.setDefault(False)

        #create layout
        layout = QGridLayout() #QVBoxLayout() vs QHBoxLayout() vs QGridLayout()
        layout.setSpacing(5)
        layout.addWidget(titleOption, 0,0)
        layout.addLayout(layoutOption, 0,1)
        layout.addWidget(title1, 1,0)
        layout.addWidget(self.lineEdit1, 1,1, 1,20) #last two ints define relative stretch conditions
        layout.addWidget(title2, 2,0)
        layout.addWidget(self.lineEdit2, 2,1, 1,20)
        layout.addWidget(title3, 3,0)
        layout.addWidget(self.lineEdit3, 3,1, 1,20)
        layout.addWidget(self.runButton,4,0)

        self.controlGroupBox.setLayout(layout)

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
    gallery.resize(1200,600)
    gallery.show()
    sys.exit(app.exec_())

