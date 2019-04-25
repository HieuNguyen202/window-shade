from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph import PlotWidget
import pyqtgraph as pg
from interface import *

# from PyQt5 import QtWidgets
from PyQt5.QtGui import QPainter, QFont
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
        MainWindow.resize(1000, 800)

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
        self.lbStatus = QtWidgets.QLabel("No status!")

        #Add widgets to menu bar


        #Add widgets to tool bar
        # self.mainToolBar.addWidget(self.connectivityWidget)

        #Add widgets to status bar
        self.statusBar.addWidget(self.lbStatus)

        #Add widgets to the layout

    def appendNode(self):
        n = NodeWidget(display=self.lbStatus)
        self.layout.addWidget(n)
        self.nodes.append(n)
        return n

    def appendUser(self):
        n = QtWidgets.QLabel("No status!")
        self.mainToolBar.addWidget(n)
        return n

    def removeNode(self, nodeUI):
        self.layout.removeWidget(nodeUI)
        self.nodes.remove(nodeUI)

COLOR_GREEN = '#00FF00'
COLOR_YELLOW = '#FFFF00'
"""Real time plot"""
class DynamicPlotWidget(PlotWidget):
    def __init__(self, sampleinterval=0.1, timewindow=10., size=(600,350), title='No title'):
        super(DynamicPlotWidget, self).__init__(title=title)
        #Setup plot
        self.resize(*size)
        self.showGrid(x=True, y=True)

        labelStyleBottom = {'color': COLOR_GREEN, 'font-size': '16pt'}
        labelStyleLeft = {'color': COLOR_YELLOW, 'font-size': '16pt'}
        titleStyle = {'color': '#FFF', 'size': '26pt'}

        self.legend = self.addLegend(size=(300, 100), offset=(0, 0))
        self.legend.anchor((0, 0), (0, 0))

        self.setTitle(title, **titleStyle)

        self.setLabel('bottom', 'Shade position', units='step', **labelStyleBottom)
        self.getAxis("bottom").setStyle(tickTextOffset=10)
        self.getAxis('bottom').setPen('g')

        self.setLabel('left', 'Light level', units='Units', **labelStyleLeft)
        self.getAxis("left").setStyle(tickTextOffset=10)
        self.getAxis('left').setPen('y')

        #Setup curve
        self.x = list()
        self.y = list()

        #Setup live view
        self.targetPosLine = self.addLine(x=0, y=None, pen=pg.mkPen('g', width=7))
        self.targetLightLine = self.addLine(x=None, y=0, pen=pg.mkPen('y', width=7))

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
    def __init__(self, min, max, interval=1, orientation=Qt.Horizontal, labels=None, parent=None, name= ''):
        super(SliderWidget, self).__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        #create widgets
        self.lbName = QtWidgets.QLabel(name)
        self.lbMax = QtWidgets.QLabel(str(min))
        self.lbMin = QtWidgets.QLabel(str(max))
        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.setRange(min, max, interval)

        #Add widgets to layout
        self.layout.addWidget(self.lbMax)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.lbMin)
        self.layout.addWidget(self.lbName)

    def setRange(self, min, max, interval):
        self.slider.setRange(min, max)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(interval)
        self.slider.setSingleStep(interval)
        self.lbMin.setText(str(min))
        self.lbMax.setText(str(max))


"""Source: https://stackoverflow.com/questions/47494305/python-pyqt4-slider-with-tick-labels"""
class LabeledSlider(QtWidgets.QWidget):
    def __init__(self, minimum, maximum, interval=1, orientation=Qt.Horizontal,
            labels=None, parent=None, name = ''):
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
            self.layout=QtWidgets.QHBoxLayout(self)
        elif orientation==Qt.Vertical:
            self.layout=QtWidgets.QVBoxLayout(self)
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
            self.sl.setMinimumWidth(200) # just to make it easier to read
        else:
            self.sl.setTickPosition(QtWidgets.QSlider.TicksLeft)
            self.sl.setMinimumHeight(200) # just to make it easier to read
        self.sl.setTickInterval(interval)
        self.sl.setSingleStep(1)

        self.layout.addWidget(self.sl)
        self.layout.addWidget(QtWidgets.QLabel(name))

    def setRange(self, min, max):
        self.sl.setMinimum(min)
        self.sl.setMaximum(max)

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

class Param(QtWidgets.QWidget):
    def __init__(self, name = 'param', defaultValue = '0', parent=None):
        super(Param, self).__init__(parent=parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(QtWidgets.QLabel(name))
        self.textEdit = QtWidgets.QTextEdit(defaultValue)
        self.setMaximumWidth(100)
        self.setMaximumHeight(50)
        self.layout.addWidget(self.textEdit)
        self.setLayout(self.layout)

    def value(self):
        return self.textEdit.toPlainText()

class State(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(State, self).__init__(parent=parent)
        self.layout = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout)
        self.states = list()

        self.lbIdle = QtWidgets.QLabel('idle')
        self.lbCal3 = QtWidgets.QLabel('Calibration 3')
        self.lbCal2 = QtWidgets.QLabel('Calibration 2')
        self.lbCal1 = QtWidgets.QLabel('Calibration 1')
        self.lbCal0 = QtWidgets.QLabel('Calibration 0')
        self.lbPPersuit = QtWidgets.QLabel('Pos Persuit')
        self.lbLPersuit = QtWidgets.QLabel('Light Persuit')
        self.lastState = self.lbIdle


        self.layout.addWidget(self.lbIdle, 1, 2)
        self.layout.addWidget(self.lbCal3, 2, 2)
        self.layout.addWidget(self.lbCal2, 3, 2)
        self.layout.addWidget(self.lbCal1, 4, 2)
        self.layout.addWidget(self.lbCal0, 5, 2)
        self.layout.addWidget(self.lbPPersuit, 1, 1)
        self.layout.addWidget(self.lbLPersuit, 1, 3)

        self.states.append(self.lbIdle)
        self.states.append(self.lbCal3)
        self.states.append(self.lbCal2)
        self.states.append(self.lbCal1)
        self.states.append(self.lbCal0)
        self.states.append(self.lbPPersuit)
        self.states.append(self.lbLPersuit)

        #middle justify all labels
        items = (self.layout.itemAt(i).widget() for i in range(self.layout.count()))
        for w in items:
            w.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            w.setFrameShape(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
            w.setLineWidth(3)
            w.setMargin(5);
        # self.setMaximumWidth(100)
        # self.setMaximumHeight(50)

    def changeState(self, s):
        self.lastState.setStyleSheet("QLabel {background:transparent}; color: black")
        self.lastState.setLineWidth(10)
        self.states[s].setStyleSheet("QLabel {background-color:green; color: white}")
        self.lastState = self.states[s]

    def value(self):
        return self.textEdit.toPlainText()

"""Contains controls (buttons, sliders) of a distributed node."""
class NodeWidget(QtWidgets.QWidget):
    def __init__(self, display = None):
        super(NodeWidget, self).__init__()
        self.display = display
        self.hLayout = QtWidgets.QHBoxLayout()
        self.vLayout = QtWidgets.QVBoxLayout()
        self.btnLayout = QtWidgets.QGridLayout()
        self.sliderLayout = QtWidgets.QGridLayout()

        self.setLayout(self.hLayout)
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
        self.btnDisconnect =  QtWidgets.QPushButton("Disconnect")
        self.btnSchedulerDemo =  QtWidgets.QPushButton("Scheduler Demo")
        self.btnStop =  QtWidgets.QPushButton("Stop")
        self.paramStep = Param(name='Step', defaultValue='200')
        self.paramKp = Param(name='Kp', defaultValue='0.3')
        self.state = State()

        self.sliderPos = SliderWidget(min=0, max=100, interval=30, orientation=Qt.Vertical, name='P')
        self.sliderLight = SliderWidget(min=0, max=100, interval=40, orientation=Qt.Vertical, name='L')

        self.plot = DynamicPlotWidget(sampleinterval=0.05, timewindow=10.)
        # self.plot.hide()

        # self.layout.addWidget(widget, row, column, rowSpan, columnSpan)
        self.btnLayout.addWidget(self.btnUp, 1, 1)
        self.btnLayout.addWidget(self.btnDown, 2, 1)
        self.btnLayout.addWidget(self.btnCalibrate, 3, 1)
        self.btnLayout.addWidget(self.btnLive, 4, 1)
        self.btnLayout.addWidget(self.btnSetMaxPos, 1, 2)
        self.btnLayout.addWidget(self.btnSetMinPos, 2, 2)
        self.btnLayout.addWidget(self.btnShowHidePlot, 3, 2)
        self.btnLayout.addWidget(self.btnReset, 4, 2)
        self.btnLayout.addWidget(self.btnTimerOff, 5, 1)
        self.btnLayout.addWidget(self.btnDisconnect, 5, 2)
        self.btnLayout.addWidget(self.btnSchedulerDemo, 6, 1)
        self.btnLayout.addWidget(self.btnStop, 6, 2)
        self.btnLayout.addWidget(self.paramStep, 7, 1)
        self.btnLayout.addWidget(self.paramKp, 7, 2)
        self.btnLayout.addWidget(self.state, 8, 1, 1, 2)

        self.sliderLayout.addWidget(self.sliderPos, 1, 1)
        self.sliderLayout.addWidget(self.sliderLight, 1, 2)

        self.vLayout.addLayout(self.btnLayout)
        self.vLayout.addLayout(self.sliderLayout)

        self.hLayout.addWidget(self.plot)
        self.hLayout.addLayout(self.vLayout)

    # def updatePosSlider(self, max):
    #     if self.sliderPos != None:
    #         self.sliderLayout.removeWidget(self.sliderPos)
    #         self.sliderPos.deleteLater()
    #         self.sliderPos = None
    #     self.sliderPos = LabeledSlider(minimum=0, maximum=max, interval=max//10, orientation=Qt.Vertical)
    #     self.sliderLayout.addWidget(self.sliderPos, 1, 1)
    #
    # def updateLightSlider(self, min, max):
    #     if self.sliderLight != None:
    #         self.sliderLayout.removeWidget(self.sliderLight)
    #         self.sliderLight.deleteLater()
    #         self.sliderLight = None
    #     self.sliderLight = LabeledSlider(minimum=min, maximum=max, interval=max//10, orientation=Qt.Vertical)
    #     self.sliderLayout.addWidget(self.sliderLight, 1, 2)

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