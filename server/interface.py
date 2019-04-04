from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket, QNetworkInterface, QAbstractSocket
from PyQt5.QtCore import pyqtSignal, QObject
MESSAGE_LENGTH = 5  #Including checksum
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
    newOutput = pyqtSignal(bytes)

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
        self.newOutput.connect(tcpClient.write)
        self.tcpClient = tcpClient
        self.tcpClientAttached()

    #Detach the tcpClient from the Node
    def detach(self):
        self.tcpClient.readyRead.disconnect(self.newInput)
        self.tcpClient.error.disconnect(self.socketError)
        self.tcpClient.error.disconnect(self.detach)
        self.newOutput.disconnect(self.tcpClient.write)
        self.tcpClient = None
        self.tcpClientDetached()

    def write(self, command, val):
        valStr = str(val).zfill(MESSAGE_LENGTH-1)
        message = command + valStr
        if len(message) > MESSAGE_LENGTH:
            raise ValueError
        self.tcpClient.write(message)

    def newInput(self):
        while self.tcpClient.bytesAvailable() >= MESSAGE_LENGTH:
            input = self.tcpClient.read(MESSAGE_LENGTH)
            if input[0] == LIGHT:
                self.newSensorData(int(input[1:]))
            elif input[0] == SHADE_POS:
                self.newShadePos(int(input[1:]))
            else:
                print('Unknown input:', input)

    def setShadePos(self, val):
        self.write(SET_SHADE_POS, val)

    '''Abstrat methods all children need to implement.'''

    def newSensorData(self, val):
        print("Need to implement newSensorData")

    def newShadePos(self, val):
        print("Need to implement newShadePos")

    def tcpClientAttached(self):
        print("Need to implement tcpClientAttached")

    def tcpClientDetached(self):
        print("Need to implement tcpClientDetached")

    def socketError(self, status):
        print("Need to implement connectionError")

"""An Node implementation that is used in a command line interface. Used in computer with no graphics"""
class CLINode(Node):
    def __init__(self, tcpClient):
        super(CLINode, self).__init__(tcpClient)

    def newSensorData(self, val):
        print(self.tcpClient.peerAddress().toString()+": newSensorData(",val,").")

    def newShadePos(self, val):
        print(self.tcpClient.peerAddress().toString()+": newShadePos(",val,").")

    def tcpClientAttached(self):
        print(self.tcpClient.peerAddress().toString()+": tcpClientAttached().")

    def tcpClientDetached(self):
        print(self.tcpClient.peerAddress().toString()+": tcpClientDetached().")

    def socketError(self, status):
        print(self.tcpClient.peerAddress().toString()+": setSharePos(",status,").")
