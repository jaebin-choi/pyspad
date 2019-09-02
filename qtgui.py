from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget)
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure





class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        self.originalPalette = QApplication.palette()
        self.createControlGroupBox()
        self.createPlotBox()
        self.createProgressBar()
        self.createPlotBox2()


        mainLayout = QGridLayout()
        mainLayout.addWidget(self.controlGroupBox, 0, 0)
        mainLayout.addWidget(self.plotBox, 1, 0)
        mainLayout.addWidget(self.progressBar, 2, 0, 1, 2)
        mainLayout.addWidget(self.plotBox2, 0, 1,2,1)

        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle("SPAD Probe Acquisition")



    def createPlotBox(self):
        self.plotBox = QGroupBox("Phase Sweep")
        figure = Figure()
        canvas = FigureCanvasQTAgg(figure)

        figure.add_subplot(111)

        layoutVertical = QVBoxLayout(self.plotBox)
        layoutVertical.addWidget(canvas)

    def createPlotBox2(self):
        self.plotBox2 = QGroupBox("SPAD Probe Image")
        figure = Figure()
        canvas = FigureCanvasQTAgg(figure)
        figure.add_subplot(211)
        figure.add_subplot(212)

        layoutVertical = QVBoxLayout(self.plotBox2)
        layoutVertical.addWidget(canvas)

        # import parse_v3
        # parse_v3
        # plt.scatter(np.tile(range(0, npix), goodframes), scatt[0:goodframes * npix], color='tab:blue')

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

        lineEdit1 = QLineEdit('bitfile directory')
        lineEdit2 = QLineEdit('save directory')
        lineEdit3 = QLineEdit('#frames')

        titleOption = QLabel("Acq Option")
        title1 = QLabel("bitfile")
        title1.setBuddy(lineEdit1)
        title2 = QLabel('savedir')
        title2.setBuddy(lineEdit2)

        title3 = QLabel('#frames')
        title3.setBuddy(lineEdit3)

        defaultPushButton = QPushButton("Run")
        defaultPushButton.setDefault(True)


        #layout = QVBoxLayout()
        layout = QGridLayout()
        layout.setSpacing(5)
        layout.addWidget(titleOption, 0,0)
        layout.addLayout(layoutOption, 0,1)
        layout.addWidget(title1, 1,0)
        layout.addWidget(lineEdit1, 1,1, 1,20)
        layout.addWidget(title2, 2,0)
        layout.addWidget(lineEdit2, 2,1, 1,20)
        layout.addWidget(title3, 3,0)
        layout.addWidget(lineEdit3, 3,1, 1,20)
        layout.addWidget(defaultPushButton,4,0)

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
    gallery = WidgetGallery()
    gallery.resize(1000,500)
    gallery.show()
    sys.exit(app.exec_())

