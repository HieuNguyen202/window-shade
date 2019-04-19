from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph import PlotWidget
import pyqtgraph as pg

# from PyQt5 import QtWidgets
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QStyle, QStyleOptionSlider
from PyQt5.QtCore import QRect, QPoint, Qt
from PyQt5.QtCore import pyqtSignal

import collections
import random
import time
import math
import numpy as np

POS_TOLERANCE = 10
LIGHT_TOLERANCE = 10

"""The mainwindow of the GUI"""
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        #Set up window
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("Window shade monitor")
        MainWindow.resize(614, 498)

        self.nodes = list()

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
        self.labelStatus = QtWidgets.QLabel("No status!")

        #Add widgets to menu bar


        #Add widgets to tool bar
        # self.mainToolBar.addWidget(self.connectivityWidget)

        #Add widgets to status bar
        self.statusBar.addWidget(self.labelStatus)

        #Add widgets to the layout

    def appendNode(self):
        n = NodeWidget()
        self.layout.addWidget(n)
        self.nodes.append(n)
        return n

"""Real time plot"""
class DynamicPlotWidget(PlotWidget):
    def __init__(self, sampleinterval=0.1, timewindow=10., size=(600,350), title='No title'):
        super(DynamicPlotWidget, self).__init__(title=title)
        #Setup plot
        self.resize(*size)
        self.showGrid(x=True, y=True)
        self.legend = self.addLegend()
        self.setLabel('left', 'Light level', '')
        self.setLabel('bottom', 'Shade position', '')

        #Setup curve
        self.x = list()
        self.y = list()

        #Setup live view
        self.targetPosLine = self.addLine(x=0, y=None, pen='g')
        self.targetLightLine = self.addLine(x=None, y=0, pen='y')
        self.curve = pg.ScatterPlotItem(self.x, self.y, pen=(255,0,0))
        self.liveCurve = pg.ScatterPlotItem(pen='w', brush='w', size=30)

        self.targetPosLine.hide()
        self.targetLightLine.hide()


        self.addItem(self.curve)
        self.addItem(self.liveCurve)
        self.legend.addItem(self.curve, name="Calibration Data")
        self.legend.addItem(self.liveCurve, name="Live Position and Light Level")
        # self.legend.addItem(self.targetPosLine, name="Target Position")
        # self.legend.addItem(self.targetLightLine, name="Target Light Level")


    def setLivePointColor(self, color):
        self.liveCurve.setBrush(color)
        self.liveCurve.setPen(color)

    def setLivePoint(self, x, y):
        if(abs(self.targetPosLine.value() - x) < POS_TOLERANCE):
            self.setLivePointColor('g')
        self.liveCurve.setData([x], [y])

    def setTargetPos(self, pos):
        self.setLivePointColor('w')
        self.targetPosLine.setValue(pos)
        self.targetPosLine.show()
        self.targetLightLine.hide()

    def setTargetLight(self, light):
        self.setLivePointColor('w')
        self.targetLightLine.setValue(light)
        self.targetLightLine.show()
        self.targetPosLine.hide()

    def append(self, x, y):
        self.x.append(x)
        self.y.append(y)
        self.curve.setData(self.x, self.y)

    def clean(self):
        self.x = list()
        self.y = list()
        self.curve.setData(self.x, self.y)

"""A slider widget with name and marks."""
class SliderWidget(QtWidgets.QWidget):
    def __init__(self, name= "Slider's Name", min = 0, max=100, numInterval = 5):
        super(SliderWidget, self).__init__()
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        #create widgets
        self.lbName = QtWidgets.QLabel(name)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)

        #setup widgets
        interval = (max - min)//numInterval
        self.slider.setRange(min, max)
        self.slider.setValue(min)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(interval)
        self.slider.setSingleStep(interval)

        #Add widgets to layout
        layout.addWidget(self.lbName, 1, 1, 1, 2)
        layout.addWidget(self.slider, 2, 1, numInterval + 1, 1)

        #Add marks numbers
        for i in range(min, max + 1, interval):
            label = QtWidgets.QLabel(str(i*interval))
            label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(label, numInterval - i +2, 2 ,1 ,1)

"""Source: https://stackoverflow.com/questions/47494305/python-pyqt4-slider-with-tick-labels"""
class LabeledSlider(QtWidgets.QWidget):
    def __init__(self, minimum, maximum, interval=1, orientation=Qt.Horizontal,
            labels=None, parent=None):
        super(LabeledSlider, self).__init__(parent=parent)

        levels=range(minimum, maximum+interval, interval)
        if labels is not None:
            if not isinstance(labels, (tuple, list)):
                raise Exception("<labels> is a list or tuple.")
            if len(labels) != len(levels):
                raise Exception("Size of <labels> doesn't match levels.")
            self.levels=list(zip(levels,labels))
        else:
            self.levels=list(zip(levels,map(str,levels)))

        if orientation==Qt.Horizontal:
            self.layout=QtWidgets.QVBoxLayout(self)
        elif orientation==Qt.Vertical:
            self.layout=QtWidgets.QHBoxLayout(self)
        else:
            raise Exception("<orientation> wrong.")

        # gives some space to print labels
        self.left_margin=10
        self.top_margin=10
        self.right_margin=10
        self.bottom_margin=10

        self.layout.setContentsMargins(self.left_margin,self.top_margin,
                self.right_margin,self.bottom_margin)

        self.sl=QtWidgets.QSlider(orientation, self)
        self.sl.setMinimum(minimum)
        self.sl.setMaximum(maximum)
        self.sl.setValue(minimum)
        if orientation==Qt.Horizontal:
            self.sl.setTickPosition(QtWidgets.QSlider.TicksBelow)
            self.sl.setMinimumWidth(300) # just to make it easier to read
        else:
            self.sl.setTickPosition(QtWidgets.QSlider.TicksLeft)
            self.sl.setMinimumHeight(300) # just to make it easier to read
        self.sl.setTickInterval(interval)
        self.sl.setSingleStep(1)

        self.layout.addWidget(self.sl)

    def paintEvent(self, e):

        super(LabeledSlider,self).paintEvent(e)

        style=self.sl.style()
        painter=QPainter(self)
        st_slider=QStyleOptionSlider()
        st_slider.initFrom(self.sl)
        st_slider.orientation=self.sl.orientation()

        length=style.pixelMetric(QStyle.PM_SliderLength, st_slider, self.sl)
        available=style.pixelMetric(QStyle.PM_SliderSpaceAvailable, st_slider, self.sl)

        for v, v_str in self.levels:

            # get the size of the label
            rect=painter.drawText(QRect(), Qt.TextDontPrint, v_str)

            if self.sl.orientation()==Qt.Horizontal:
                # I assume the offset is half the length of slider, therefore
                # + length//2
                x_loc=QStyle.sliderPositionFromValue(self.sl.minimum(),
                        self.sl.maximum(), v, available)+length//2

                # left bound of the text = center - half of text width + L_margin
                left=x_loc-rect.width()//2+self.left_margin
                bottom=self.rect().bottom()

                # enlarge margins if clipping
                if v==self.sl.minimum():
                    if left<=0:
                        self.left_margin=rect.width()//2-x_loc
                    if self.bottom_margin<=rect.height():
                        self.bottom_margin=rect.height()

                    self.layout.setContentsMargins(self.left_margin,
                            self.top_margin, self.right_margin,
                            self.bottom_margin)

                if v==self.sl.maximum() and rect.width()//2>=self.right_margin:
                    self.right_margin=rect.width()//2
                    self.layout.setContentsMargins(self.left_margin,
                            self.top_margin, self.right_margin,
                            self.bottom_margin)

            else:
                y_loc=QStyle.sliderPositionFromValue(self.sl.minimum(),
                        self.sl.maximum(), v, available, upsideDown=True)

                bottom=y_loc+length//2+rect.height()//2+self.top_margin-3
                # there is a 3 px offset that I can't attribute to any metric

                left=self.left_margin-rect.width()
                if left<=0:
                    self.left_margin=rect.width()+2
                    self.layout.setContentsMargins(self.left_margin,
                            self.top_margin, self.right_margin,
                            self.bottom_margin)

            pos=QPoint(left, bottom)
            painter.drawText(pos, v_str)

        return

"""Contains controls (buttons, sliders) of a distributed node."""
class NodeWidget(QtWidgets.QWidget):
    def __init__(self):
        super(NodeWidget, self).__init__()
        self.layout = QtWidgets.QGridLayout()
        self.layoutBtn = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        # self.layout.setAlignment(pg.QtCore.Qt.AlignCenter)

        #Create button and sliders
        self.btnUp =            QtWidgets.QPushButton("Up")
        self.btnDown =          QtWidgets.QPushButton("Down")
        self.btnSetMaxPos =     QtWidgets.QPushButton("Set Max Pos")
        self.btnSetMinPos =     QtWidgets.QPushButton("Set Min Pos")
        self.btnCalibrate =     QtWidgets.QPushButton("Calibrate")
        self.btnShowHidePlot =  QtWidgets.QPushButton("Plot")
        self.btnLive =  QtWidgets.QPushButton("Live On")
        self.btnReset =  QtWidgets.QPushButton("Reset")
        self.btnTimerOff =  QtWidgets.QPushButton("TimerOff")


        self.sliderPos = None
        self.sliderLight = None
        self.plot = DynamicPlotWidget(sampleinterval=0.05, timewindow=10.)
        self.plot.hide()

        # self.layout.addWidget(widget, row, column, rowSpan, columnSpan)
        self.layout.addWidget(self.plot, 1, 1, 1, 3)

        self.layoutBtn.addWidget(self.btnUp, 1, 1)
        self.layoutBtn.addWidget(self.btnDown, 2, 1)
        self.layoutBtn.addWidget(self.btnCalibrate, 3, 1)
        self.layoutBtn.addWidget(self.btnLive, 4, 1)
        self.layoutBtn.addWidget(self.btnSetMaxPos, 1, 2)
        self.layoutBtn.addWidget(self.btnSetMinPos, 2, 2)
        self.layoutBtn.addWidget(self.btnShowHidePlot, 3, 2)
        self.layoutBtn.addWidget(self.btnReset, 4, 2)
        self.layoutBtn.addWidget(self.btnTimerOff, 5, 1)

        self.layout.addLayout(self.layoutBtn, 2, 1)

    def updatePosSlider(self, max):
        if self.sliderPos != None:
            self.layout.removeWidget(self.sliderPos)
        self.sliderPos = LabeledSlider(minimum=0, maximum=max, interval=max//10, orientation=Qt.Vertical)
        self.layout.addWidget(self.sliderPos, 2, 2)

    def updateLightSlider(self, min, max):
        if self.sliderLight != None:
            self.layout.removeWidget(self.sliderLight)
        self.sliderLight = LabeledSlider(minimum=min, maximum=max, interval=max//10, orientation=Qt.Vertical)
        self.layout.addWidget(self.sliderLight, 2, 3)

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