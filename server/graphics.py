from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph import PlotWidget

import collections
import random
import time
import math
import numpy as np

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        #Set up window
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("Window shade monitor")
        MainWindow.resize(614, 498)

        #Set up central widget
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        MainWindow.setCentralWidget(self.centralWidget)

        #Set up layout
        self.layout = QtWidgets.QGridLayout()
        self.layout.setSpacing(0)
        self.centralWidget.setLayout(self.layout)

        #Setup status bar
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        #Setup menu bar
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setObjectName("menuBar")
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 614, 22))
        MainWindow.setMenuBar(self.menuBar)

        #Setup tool bar
        self.mainToolBar = QtWidgets.QToolBar(MainWindow)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)

        #Set up widgets
        self.m = DynamicPlotWidget(sampleinterval=0.05, timewindow=10.)
        self.labelStatus = QtWidgets.QLabel("No status!")


        #Add widgets to menu bar


        #Add widgets to tool bar
        # self.mainToolBar.addWidget(self.connectivityWidget)

        #Add widgets to status bar
        self.statusBar.addWidget(self.labelStatus)

        #Add widgets to the layout
        self.layout.addWidget(self.m, 1, 1)

class DynamicPlotWidget(PlotWidget):
    def __init__(self, sampleinterval=0.1, timewindow=10., size=(600,350), title='Give me a title!'):
        super(DynamicPlotWidget, self).__init__(title=title)
        # Data stuff
        self._interval = int(sampleinterval*1000)
        self._bufsize = int(timewindow/sampleinterval)
        self.databuffer = collections.deque([0.0]*self._bufsize, self._bufsize)
        self.x = np.linspace(-timewindow, 0.0, self._bufsize)
        self.y = np.zeros(self._bufsize, dtype=np.float)

        # PyQtGraph stuff
        self.resize(*size)
        self.showGrid(x=True, y=True)
        self.setLabel('left', 'amplitude', 'V')
        self.setLabel('bottom', 'time', 's')

        self.curve = self.plot(self.x, self.y, pen=(255,0,0))

    def appendData(self, data):
        self.databuffer.append(data)
        self.y[:] = self.databuffer
        self.curve.setData(self.x, self.y)

def getdata():
    global m
    frequency = 0.5
    noise = random.normalvariate(0., 1.)
    new = 10. * math.sin(time.time() * frequency * 2 * math.pi) + noise
    return new

if __name__ == '__main__':
    app = QtGui.QApplication([])
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: ui.m.appendData(getdata()))
    timer.start(1000)
    app.exec_()