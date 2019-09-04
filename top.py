import sys
import os

from spadGuiLauncher import spadGui
from PyQt5 import QtCore, QtWidgets, QtGui

# import LogManager
# import Constants
# import LogFile

constants = Constants.Instance()

if __name__ == "__main__":
	if os.path.isfile(constants.LOG_FILE_NAME) :
		os.remove(constants.LOG_FILE_NAME)
	# logFile = LogFile.LogFile(constants.LOG_FILE_NAME, 'a')
	# LogManager.Instance().addLogMethod(logFile.writeLog, 1)
	app = QtWidgets.QApplication(sys.argv)
	app.setStyle("fusion")
	myapp = Costi()
	myapp.show()
	result = app.exec_()

	# Wait for the opal kelly components to clean itself properly
	# Otherwise core dump is likely to be raised
	#time.sleep(0.1)

	#logFile.close()
	sys.exit(result)