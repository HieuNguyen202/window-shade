from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket, QNetworkInterface, QAbstractSocket
from PyQt5.QtCore import pyqtSignal, QObject
MESSAGE_LENGTH = 6  #Including checksum
LIGHT = 'l'
SHADE_POS = 'p'
SET_SHADE_POS = 'p'

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
    def __init__(self):
        super(Server, self).__init__()
        self.newConnection.connect(self.acceptConnection)
        self.acceptError.connect(self.acceptErrorHandler)
        if not self.listen(address=QHostAddress.Any, port=1234):
            print("interface.py: Unable to start the server: ", self.errorString())
            return
        ipAddress = getIPAddress()
        print('interface.py: The server is running on', ipAddress, 'port', self.serverPort())

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
    newPosUpperLimit = pyqtSignal(int)
    newLightUpperLimit = pyqtSignal(int)
    newPosLowerLimit = pyqtSignal(int)
    newLightLowerLimit = pyqtSignal(int)
    newCalibrate = pyqtSignal(int)
    newSetPos = pyqtSignal(int)
    newSetLight = pyqtSignal(int)
    newSetModeSensor = pyqtSignal(int)
    newSetModeLight = pyqtSignal(int)

    def __init__(self, tcpClient):
        super(Node, self).__init__()
        self.tcpClient = None
        self.attach(tcpClient)
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
        self.tcpClient.readyRead.disconnect(self.newInput)
        self.tcpClient.error.disconnect(self.socketError)
        self.tcpClient.error.disconnect(self.detach)
        self.tcpClient = None
        self.tcpClientDetached()

    def combine(self, command, val):
        valStr = str(val).zfill(MESSAGE_LENGTH-len(command))
        message = command + valStr
        if len(message) > MESSAGE_LENGTH:
            raise ValueError
        return message

    def write(self, message):
        self.tcpClient.write(message.encode())

    def newInput(self):
        while self.tcpClient.bytesAvailable() >= MESSAGE_LENGTH:
            input = self.tcpClient.read(MESSAGE_LENGTH).decode()
            if input[0] == 'g':
                val = int(input[2:])
                if input[1] == '1':
                    self.newPos.emit(val)
                if input[1] == '2':
                    self.newLight.emit(val)
                if input[1] == '3':
                    self.newPosMax.emit(val)
                if input[1] == '4':
                    self.newLightMax.emit(val)
                if input[1] == '5':
                    self.newPosUpperLimit.emit(val)
                if input[1] == '6':
                    self.newLightUpperLimit.emit(val)
                if input[1] == '7':
                    self.newPosLowerLimit.emit(val)
                if input[1] == '8':
                    self.newLightLowerLimit.emit(val)
            elif input[0] == 'c':
                status = input[MESSAGE_LENGTH - 1]  #last digit
                self.newCalibrate.emit(int(status))
            elif input[0] == 's':
                val = int(input[2:])
                if input[1] == '1':
                    self.newSetPos.emit(val)
                if input[1] == '2':
                    self.newSetLight.emit(val)
                if input[1] == '3':
                    self.newSetModeSensor.emit(val)
                if input[1] == '4':
                    self.newSetModeLight.emit(val)
            else:
                print('Unknown input:', input)

    def tcpClientAttached(self):
        print("Need to implement tcpClientAttached")

    def tcpClientDetached(self):
        print("Need to implement tcpClientDetached")

    def socketError(self, status):
        print("Need to implement connectionError")

    def getPos(self, ):
        self.write("g10000")

    def getLight(self, ):
        self.write("g20000")

    def getPosMax(self, ):
        self.write("g30000")

    def getLightMax(self, ):
        self.write("g40000")

    def getPosUpperLimit(self, ):
        self.write("g50000")

    def getLightUpperLimit(self, ):
        self.write("g60000")

    def getPosLowerLimit(self, ):
        self.write("g70000")

    def getLightLowerLimit(self, ):
        self.write("g80000")

    def calibrate(self, ):
        self.write("c00000")

    def setPos(self, pos):
        self.write(self.combine("s1", pos))

    def setLight(self, light):
        self.write(self.combine("s2", light))

    """interval = 0: on demand
    interval > 0: internal between messages in seconds"""
    def setModeSensor(self, interval):
        self.write(self.combine("s3", interval))

    """interval = 0: on demand
    interval > 0: internal between messages in seconds"""
    def setModeLight(self, interval):
        self.write(self.combine("s4", interval))

"""An Node implementation that is used in a command line interface. Used in computer with no graphics"""
class CLINode(Node):
    def __init__(self, tcpClient):
        super(CLINode, self).__init__(tcpClient)
        self.newPos.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPos(", val,")"))
        self.newLight.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLight(", val,")"))
        self.newPosMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosMax(", val,")"))
        self.newLightMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightMax(", val,")"))
        self.newPosUpperLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosUpperLimit(", val,")"))
        self.newLightUpperLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightUpperLimit(", val,")"))
        self.newPosLowerLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosLowerLimit(", val,")"))
        self.newLightLowerLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightLowerLimit(", val,")"))
        self.newCalibrate.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newCalibrate(", val,")"))
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
    def __init__(self, tcpClient, ui):
        super(GUINode, self).__init__(tcpClient)
        self.ui = ui
        self.newPos.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPos(", val,")"))
        self.newLight.connect(self.ui.plot.appendData)
        self.newPosMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosMax(", val,")"))
        self.newLightMax.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightMax(", val,")"))
        self.newPosUpperLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosUpperLimit(", val,")"))
        self.newLightUpperLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightUpperLimit(", val,")"))
        self.newPosLowerLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newPosLowerLimit(", val,")"))
        self.newLightLowerLimit.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newLightLowerLimit(", val,")"))
        self.newCalibrate.connect(lambda val: print(self.tcpClient.peerAddress().toString() + ": newCalibrate(", val,")"))
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
