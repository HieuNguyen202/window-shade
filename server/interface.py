from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket, QNetworkInterface, QAbstractSocket
from PyQt5.QtCore import pyqtSignal, QObject, QTimer
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
MESSAGE_LENGTH = 6  #Including checksum
LIGHT = 'l'
SHADE_POS = 'p'
SET_SHADE_POS = 'p'
import struct
from enum import Enum
from graphics import *

"""Get the IP address of the host computer."""
def getIPAddress():
    for ipAddress in QNetworkInterface.allAddresses():
        if ipAddress != QHostAddress.LocalHost and ipAddress.toIPv4Address() != 0:
            break
    else:
        ipAddress = QHostAddress(QHostAddress.LocalHost)
    return ipAddress.toString()

"""Represent the central node. accept and process TCP request from distributed nodes."""
class Server(QTcpServer):
    newClient = pyqtSignal(QTcpSocket)
    startedListening = pyqtSignal(str, int)
    failedToListen = pyqtSignal(str)
    def __init__(self):
        super(Server, self).__init__()
        self.newConnection.connect(self.acceptConnection)
        self.acceptError.connect(self.acceptErrorHandler)

    def startListening(self, port):
        if not self.listen(address=QHostAddress.Any, port=port):
            self.failedToListen.emit(self.errorString())
        else:
            self.startedListening.emit(getIPAddress(), port)

    def acceptConnection(self):
        self.newClient.emit(self.nextPendingConnection())

    def acceptErrorHandler(self, socketError):
        print("interface.py: Server accept error", socketError)

"""Represent a distributed node. Contains interfaces to interact with the distributed nodes."""
class Node(QObject):
    newPos = pyqtSignal(int)
    newLight = pyqtSignal(int)
    newPosMax = pyqtSignal(int)
    newLightMax = pyqtSignal(int)
    newUpperBoundPosAndLight = pyqtSignal(int, int)
    newLightUpperLimit = pyqtSignal(int)
    newLowerBoundPosAndLight = pyqtSignal(int, int)
    newLightLowerLimit = pyqtSignal(int)
    newCalibrateStatus = pyqtSignal(int)
    newGetState = pyqtSignal(int)
    newSetPos = pyqtSignal(int)
    newSetLight = pyqtSignal(int)
    newGetMinLight = pyqtSignal(int)
    newSetModeSensor = pyqtSignal(int)
    newSetModeLight = pyqtSignal(int)
    newSetMinPos = pyqtSignal(int)
    newGetMinPos = pyqtSignal(int)
    newSetMaxPos = pyqtSignal(int)
    newSetStepIncrement = pyqtSignal(int)
    newPosAndLight = pyqtSignal(int, int)
    newLivePosAndLight = pyqtSignal(int, int)

    CAL_STATUS_SUCCESSFUL = 0
    CAL_STATUS_TIMEOUT = 1
    CAL_STATUS_LIMIT_NOT_SET = 2
    CAL_STATUS_IN_STAGE0 = 3
    CAL_STATUS_IN_STAGE1 = 4
    CAL_STATUS_IN_STAGE2 = 5
    CAL_STATUS_IN_STAGE3 = 6

    def __init__(self, tcpClient):
        super(Node, self).__init__()
        self.tcpClient = None
        self.attach(tcpClient)
        self.targetLight = None
        self.curLight = None
        self.curPos = None
        self.kp = 0.4
        self.maxPos = None
        self.minPos = None
        self.maxLight = None
        self.minLight = None

    '''Methods to be used by the the child classes'''

    def attach(self, tcpClient):
        if self.tcpClient != None:
            self.detach()
        tcpClient.readyRead.connect(self.newInput)
        tcpClient.error.connect(self.socketError)
        tcpClient.error.connect(self.detach)
        self.tcpClient = tcpClient
        self.tcpClientAttached()

    #Detach the tcpClient from the Node
    def detach(self):
        try:
            self.tcpClient.readyRead.disconnect(self.newInput)
            self.tcpClient.error.disconnect(self.socketError)
            self.tcpClient.error.disconnect(self.detach)
            self.tcpClientDetached()
            self.tcpClient = None
        except:
            pass

    def write(self, command, value1, value2):
        self.tcpClient.write(struct.pack("Hhh", command.value, value1, value2))

    def newInput(self):
        while self.tcpClient.bytesAvailable() >= MESSAGE_LENGTH:
            raw = self.tcpClient.read(MESSAGE_LENGTH)
            message = struct.unpack('Bhh', raw)
            command = message[0]
            value1 = message[1]
            value2 = message[2]
            if   command == Commands.CMD_GET_STATE.value: self.newGetState.emit(value1)
            elif command == Commands.CMD_GET_POS.value: self.newPos.emit(value1)
            elif command == Commands.CMD_GET_LIGHT.value: self.newLight.emit(value1)
            elif command == Commands.CMD_GET_POS_AND_LIGHT.value: self.newPosAndLight.emit(value1, value2) #pos, light
            elif command == Commands.CMD_GET_MAX_POS.value: self.newPosMax.emit(value1)
            elif command == Commands.CMD_GET_MAX_LIGHT.value: self.newLightMax.emit(value1)
            elif command == Commands.CMD_GET_MIN_POS.value: self.newGetMinPos.emit(value1)
            elif command == Commands.CMD_GET_MIN_LIGHT.value: self.newGetMinLight.emit(value1)
            elif command == Commands.CMD_GET_LOWER_BOUND_POS_AND_LIGHT.value: self.newLowerBoundPosAndLight.emit(value1, value2)
            elif command == Commands.CMD_GET_UPPER_BOUND_POS_AND_LIGHT.value: self.newUpperBoundPosAndLight.emit(value1, value2)
            elif command == Commands.CMD_SET_POS.value: self.newSetPos.emit(value1)
            elif command == Commands.CMD_SET_LIGHT.value: self.newSetLight.emit(value1)
            elif command == Commands.CMD_SET_MIN_POS.value: self.newSetMinPos.emit(value1)
            elif command == Commands.CMD_SET_MAX_POS.value: self.newSetMaxPos.emit(value1)
            elif command == Commands.CMD_SET_STEP_INCREMENT.value: self.newSetStepIncrement.emit(value1)
            elif command == Commands.CMD_CALIBRATE.value: self.newCalibrateStatus.emit(value1)
            elif command == Commands.CMD_GET_LIVE_POS_AND_LIGHT.value: self.newLivePosAndLight.emit(value1, value2)
            else: print("Unknown message: ", message)

    def tcpClientAttached(self):
        print("Need to implement tcpClientAttached")

    def tcpClientDetached(self):
        print("Need to implement tcpClientDetached")

    def socketError(self, status):
        print("Need to implement connectionError")

    def getPos(self):
        self.write(Commands.CMD_GET_POS, 0, 0)

    def getLivePosAndLight(self, on, intervalMilis):
        self.write(Commands.CMD_GET_LIVE_POS_AND_LIGHT, on, intervalMilis)

    def getLight(self):
        self.write(Commands.CMD_GET_LIGHT, 0, 0)

    def getPosMax(self):
        self.write(Commands.CMD_GET_MAX_POS, 0, 0)

    def getLightMax(self):
        self.write(Commands.CMD_GET_MAX_LIGHT, 0, 0)

    def getUpperBoundPosAndLight(self):
        self.write(Commands.CMD_GET_UPPER_BOUND_POS_AND_LIGHT, 0, 0)

    def getMaxLight(self):
        self.write(Commands.CMD_GET_MAX_LIGHT, 0, 0)

    def getMinLight(self):
        self.write(Commands.CMD_GET_MIN_LIGHT, 0, 0)

    def calibrate(self, timeout, numInterval):
        self.write(Commands.CMD_CALIBRATE, timeout, numInterval)

    def setPos(self, pos):
        self.write(Commands.CMD_SET_POS, pos, 0)

    def setPosByUser(self, pos):
        print('setPosByUser')
        if self.minPos == None or self.maxPos == None:
            return
        mPos = self.map(pos, 0, 100, self.minPos, self.maxPos)
        self.setPos(mPos)

    def setLightByUser(self, light):
        print('setLightByUser')
        if self.minLight == None or self.maxLight == None:
            return
        mLight = self.map(light, 0, 100, self.minLight, self.maxLight)
        self.setLight(mLight)

    def setLight(self, light):
        self.write(Commands.CMD_SET_LIGHT, light, 0)

    def setMinPos(self):
        self.write(Commands.CMD_SET_MIN_POS, 0, 0)

    def setMaxPos(self):
        self.write(Commands.CMD_SET_MAX_POS, 0, 0)

    def step(self, steps):
        self.write(Commands.CMD_SET_STEP_INCREMENT, steps, 0)

    def stepByUser(self, steps):
        print('stepByUser')
        if self.minPos == None or self.maxPos == None:
            return
        mSteps = self.map(steps, 0, 100, self.minPos, self.maxPos)
        self.write(Commands.CMD_SET_STEP_INCREMENT, mSteps, 0)
        self.step(mSteps)

    def reset(self):
        self.write(Commands.CMD_RESET, 0, 0)

    def map(sefl, x, in_min, in_max, out_min, out_max):
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

"""An Node implementation that is used in a command line interface. Used in computer with no graphics"""
class CLINode(Node):
    def __init__(self, tcpClient):
        super(CLINode, self).__init__(tcpClient)
        self.newPos.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPos(", val,")"))
        self.newLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLight(", val,")"))
        self.newPosMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosMax(", val,")"))
        self.newLightMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightMax(", val,")"))
        self.newUpperBoundPosAndLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosUpperLimit(", val, ")"))
        self.newLightUpperLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightUpperLimit(", val,")"))
        self.newLowerBoundPosAndLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosLowerLimit(", val, ")"))
        self.newLightLowerLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightLowerLimit(", val,")"))
        self.newCalibrateStatus.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newCalibrate(", val, ")"))
        self.newSetPos.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetPos(", val,")"))
        self.newSetLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetLight(", val,")"))
        self.newSetModeSensor.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetModeSensor(", val,")"))
        self.newSetModeLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetModeLight(", val,")"))

    def tcpClientAttached(self):
        print(self.tcpClient.peerAddress().toString()+": tcpClientAttached().")

    def tcpClientDetached(self):
        print(self.tcpClient.peerAddress().toString()+": tcpClientDetached().")

    def socketError(self, status):
        print(self.tcpClient.peerAddress().toString()+": setSharePos(",status,").")

"""An Node implementation that is used in a command line interface. Used in computer with no graphics"""
class GUINode(Node):
    closeBtnPressed = pyqtSignal(NodeWidget)
    def __init__(self, tcpClient, nodeUI:NodeWidget):
        super(GUINode, self).__init__(tcpClient)
        self.timer = QTimer()
        self.interval = 500 #ms
        self.timer.timeout.connect(self.persuitLight)

        self.nodeUI = nodeUI
        self.nodeUI.plot.plotItem.setTitle(tcpClient.peerAddress().toString()[7:])
        self.newPos.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPos(", val,")"))
        # self.newLight.connect(self.ui.plot.appendData)
        self.newPosMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosMax(", val,")"))
        self.newLightMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightMax(", val,")"))
        self.newUpperBoundPosAndLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosUpperLimit(", val, ")"))
        self.newLightUpperLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightUpperLimit(", val,")"))
        self.newLowerBoundPosAndLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosLowerLimit(", val, ")"))
        self.newLightLowerLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightLowerLimit(", val,")"))
        self.newCalibrateStatus.connect(self.newCalibrateStatusHandler)
        self.newSetPos.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetPos(", val,")"))
        self.newSetLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetLight(", val,")"))
        self.newSetModeSensor.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetModeSensor(", val,")"))
        self.newSetModeLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newSetModeLight(", val,")"))
        self.newSetMinPos.connect(self.newSetMinPosHandler)
        self.newSetMaxPos.connect(self.newSetMaxPosHandler)
        self.newSetStepIncrement.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newStep(", val, ")"))
        self.newPosAndLight.connect(self.nodeUI.plot.append)
        self.newGetState.connect(self.nodeUI.state.changeState)
        self.newLivePosAndLight.connect(self.newLivePosAndLightHandler)

        self.nodeUI.btnSetMinPos.pressed.connect(self.setMinPos)
        self.nodeUI.btnSetMaxPos.pressed.connect(self.setMaxPos)
        self.nodeUI.btnCalibrate.pressed.connect(self.calibrateBtnHandler)
        self.nodeUI.btnLive.pressed.connect(self.liveBtnHandler)
        self.nodeUI.btnReset.pressed.connect(self.resetBtnHandler)
        self.nodeUI.btnTimerOff.pressed.connect(self.timer.stop)
        self.nodeUI.btnDisconnect.pressed.connect(self.disconnectBtnHandler)

        # self.buttonDeliver.pressed.connect(lambda: self.buttonDeliverPressed.emit(self.slider.slider.value()))
        self.nodeUI.btnUp.pressed.connect(lambda: self.step(int(self.nodeUI.paramStep.value())))
        self.nodeUI.btnDown.pressed.connect(lambda: self.step(-int(self.nodeUI.paramStep.value())))

        self.nodeUI.sliderPos.slider.sliderReleased.connect(self.posSliderReleaseHandler)
        self.nodeUI.sliderLight.slider.sliderReleased.connect(self.lightSliderReleaseHandler)

    def newSetMinPosHandler(self, pos):
        self.minPos = pos

    def newSetMaxPosHandler(self, pos):
        self.maxPos = pos
        self.updatePosSlider(pos)

    def newLivePosAndLightHandler(self, pos, light):
        self.nodeUI.plot.setLivePoint(x=pos, y=light)
        self.curPos = pos
        self.curLight = light

    def disconnectBtnHandler(self):
        self.detach()
        print("closed")
        self.closeBtnPressed.emit(self.nodeUI)

    def resetBtnHandler(self):
        self.reset()

    def calibrateBtnHandler(self):
        self.nodeUI.plot.show()
        self.nodeUI.plot.clean()
        self.calibrate(timeout=20, numInterval=100)

    def liveBtnHandler(self):
        if self.nodeUI.btnLive.text() == "Live On": #live
            self.nodeUI.plot.liveCurve.show()
            self.getLivePosAndLight(on=1, intervalMilis=100)
            self.nodeUI.btnLive.setText("Live Off")
        else:   #Not Live
            self.nodeUI.plot.liveCurve.hide()
            self.getLivePosAndLight(on=0, intervalMilis=0)
            self.nodeUI.btnLive.setText("Live On")
            self.targetLight = None

    def newCalibrateStatusHandler(self, status):
        if (status == self.CAL_STATUS_SUCCESSFUL):
            print(min(self.nodeUI.plot.y))
            self.minLight = min(self.nodeUI.plot.y)
            self.maxLight = max(self.nodeUI.plot.y)
            self.updateLightSlider(self.minLight, self.maxLight)
            print("Calibration Status: CAL_STATUS_SUCCESSFUL")
        elif (status == self.CAL_STATUS_TIMEOUT):
            print("Calibration Status: CAL_STATUS_TIMEOUT")
        elif (status == self.CAL_STATUS_LIMIT_NOT_SET):
            print("Calibration Status: CAL_STATUS_LIMIT_NOT_SET")
        elif (status == self.CAL_STATUS_IN_STAGE0):
            print("Calibration Status: CAL_STATUS_IN_STAGE0")
        elif (status == self.CAL_STATUS_IN_STAGE1):
            print("Calibration Status: CAL_STATUS_IN_STAGE1")
        elif (status == self.CAL_STATUS_IN_STAGE2):
            print("Calibration Status: CAL_STATUS_IN_STAGE2")
        elif (status == self.CAL_STATUS_IN_STAGE3):
            print("Calibration Status: CAL_STATUS_IN_STAGE3")
        else:
            print("Calibration Status: UNKNOWN")

    def posSliderReleaseHandler(self):
        val = self.nodeUI.sliderPos.slider.value()      #current slider's value
        self.setPos(val)                        #execution
        self.nodeUI.plot.setTargetPos(val)          #Display

    def lightSliderReleaseHandler(self):
        val = self.nodeUI.sliderLight.slider.value()    #current slider's value
        self.nodeUI.plot.setTargetLight(val)        #Display
        #execution
        self.getLivePosAndLight(on=1, intervalMilis=100)
        self.targetLight = val
        self.timer.setInterval(self.interval)
        self.timer.start()

    def persuitLight(self):
        if self.targetLight is None:
            self.timer.stop()
            return
        if self.curLight is not None:
            diff = self.curLight - self.targetLight
            if(abs(diff) < LIGHT_TOLERANCE):
                self.nodeUI.plot.setLivePointColor('y')
                self.timer.stop()
            else:
                step = int(diff * self.kp)
                print(-step)
                self.step(-step)

    def updateLightSlider(self, min, max):
        self.nodeUI.sliderLight.setRange(min, max, (max-min)//10)

    def updatePosSlider(self, max):
        self.nodeUI.sliderPos.setRange(0, max, max//10)

    def tcpClientAttached(self):
        print(self.tcpClient.peerAddress().toString()+": tcpClientAttached().")

    def tcpClientDetached(self):
        print(self.tcpClient.peerAddress().toString()+": tcpClientDetached().")

    def socketError(self, status):
        print(self.tcpClient.peerAddress().toString()+": setSharePos(",status,").")


class UserNode(Node):
    def __init__(self, tcpClient, nodeUI):
        super(UserNode, self).__init__(tcpClient)
        self.nodeUI = nodeUI
        self.nodeUI.setText('User: ' + tcpClient.peerAddress().toString()[7:])

    def connectToShade(self, shade:GUINode):
        self.newSetPos.connect(shade.setPosByUser)
        self.newSetLight.connect(shade.setLightByUser)
        self.newSetStepIncrement.connect(shade.stepByUser)

    def tcpClientAttached(self):
        print(self.tcpClient.peerAddress().toString() + ": tcpClientAttached().")

    def tcpClientDetached(self):
        print(self.tcpClient.peerAddress().toString() + ": tcpClientDetached().")

    def socketError(self, status):
        print(self.tcpClient.peerAddress().toString() + ": setSharePos(", status, ").")

class Commands(Enum):
    CMD_GET_STATE = 0
    CMD_GET_POS = 1
    CMD_GET_LIGHT = 2
    CMD_GET_POS_AND_LIGHT = 3
    CMD_GET_MAX_POS = 4
    CMD_GET_MAX_LIGHT = 5
    CMD_GET_MIN_POS = 6
    CMD_GET_MIN_LIGHT = 7
    CMD_GET_LOWER_BOUND_POS_AND_LIGHT = 8
    CMD_GET_UPPER_BOUND_POS_AND_LIGHT = 9
    CMD_SET_POS = 10
    CMD_SET_LIGHT = 11
    CMD_SET_MIN_POS = 12
    CMD_SET_MAX_POS = 13
    CMD_SET_STEP_INCREMENT = 14
    CMD_CALIBRATE = 15
    CMD_GET_LIVE_POS_AND_LIGHT = 16
    CMD_RESET = 17

class States(Enum):
    IDLE = 0
    CAL_0 = 1
    CAL_1 = 2
    CAL_2 = 3
    CAL_3 = 4
    POS_PERSUIT = 5
    LIGHT_PERSUIT = 6