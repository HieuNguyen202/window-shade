from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph import PlotWidget

import collections
import random
import time
import math
import numpy as np

"""The mainwindow of the GUI"""
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
        self.node = NodeWidget()
        self.labelStatus = QtWidgets.QLabel("No status!")

        #Add widgets to menu bar


        #Add widgets to tool bar
        # self.mainToolBar.addWidget(self.connectivityWidget)

        #Add widgets to status bar
        self.statusBar.addWidget(self.labelStatus)

        #Add widgets to the layout

        self.layout.addWidget(self.node)

"""Real time plot"""
class DynamicPlotWidget(PlotWidget):
    def __init__(self, sampleinterval=0.1, timewindow=10., size=(600,350), title=''):
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

"""A slider widget with name and marks."""
class SliderWidget(QtWidgets.QWidget):
    def __init__(self, name = "Slider's Name", minVal = 0, maxVal=100):
        super(SliderWidget, self).__init__()
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        #create widgets
        self.lbName = QtWidgets.QLabel(name)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)

        #setup widgets
        numInterval = 5
        interval = (maxVal - minVal)//numInterval

        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(interval)

        #Add widgets to layout
        self.layout.addWidget(self.lbName, 1, 1, 1, 2)
        self.layout.addWidget(self.slider, 2, 1, numInterval + 1, 1)
        #Add marks numbers
        for i in range(numInterval + 1):
            label = QtWidgets.QLabel(str(i*interval))
            label.setAlignment(QtCore.Qt.AlignCenter)
            self.layout.addWidget(label, i+2,2 ,1 ,1)

"""Contains controls (buttons, sliders) of a distributed node."""
class NodeWidget(QtWidgets.QWidget):
    def __init__(self):
        super(NodeWidget, self).__init__()
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        # self.layout.setAlignment(pg.QtCore.Qt.AlignCenter)

        #Create button and sliders
        self.btnUp =            QtWidgets.QPushButton("Up")
        self.btnDown =          QtWidgets.QPushButton("Down")
        self.btnSetMaxPos =     QtWidgets.QPushButton("Set Max Pos")
        self.btnSetMinPos =     QtWidgets.QPushButton("Set Min Pos")
        self.btnCalibrate =     QtWidgets.QPushButton("Calibrate")
        self.btnShowHidePlot =  QtWidgets.QPushButton("Plot")

        self.sliderPos = SliderWidget("Shade Pos")
        self.sliderLight = SliderWidget("Light")
        self.plot = DynamicPlotWidget(sampleinterval=0.05, timewindow=10.)

        # self.layout.addWidget(widget, row, column, rowSpan, columnSpan)
        self.layout.addWidget(self.plot, 1, 1, 1, 4)
        self.layout.addWidget(self.sliderPos, 2, 3, 3, 1)
        self.layout.addWidget(self.sliderLight, 2, 4, 3, 1)
        self.layout.addWidget(self.btnUp, 2, 1)
        self.layout.addWidget(self.btnDown, 3, 1)
        self.layout.addWidget(self.btnSetMaxPos, 2, 2)
        self.layout.addWidget(self.btnSetMinPos, 3, 2)
        self.layout.addWidget(self.btnCalibrate, 4, 1)
        self.layout.addWidget(self.btnShowHidePlot, 4, 2)

        # self.buttonDeliver.pressed.connect(lambda: self.buttonDeliverPressed.emit(self.slider.slider.value()))
        # self.buttonBack.pressed.connect(lambda: self.buttonBackPressed.emit(-self.slider.slider.value()))
        # self.buttonStop.pressed.connect(lambda: self.buttonStopPressed.emit(0))

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
    timer.timeout.connect(lambda: ui.node.plot.appendData(getdata()))
    timer.start(1000)
    app.exec_()