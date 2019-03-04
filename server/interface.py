from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket, QNetworkInterface, QAbstractSocket
from PyQt5.QtCore import QObject, pyqtSignal
import struct
MESSAGE_LENGTH = 5  #Including checksum

def getIPAddress():
    for ipAddress in QNetworkInterface.allAddresses():
        if ipAddress != QHostAddress.LocalHost and ipAddress.toIPv4Address() != 0:
            break
    else:
        ipAddress = QHostAddress(QHostAddress.LocalHost)
    return ipAddress.toString()

class RobotServer(QObject):
    controllerDisconnected = pyqtSignal()
    newConnection = pyqtSignal(QTcpSocket)
    newMessage = pyqtSignal(bytes)

    def __init__(self):
        super(RobotServer, self).__init__()
        self.tcpServer = QTcpServer()
        self.tcpServer.newConnection.connect(self.acceptConnection)
        self.tcpServer.acceptError.connect(self.acceptError)
        self.clients = list()
        if not self.tcpServer.listen(address=QHostAddress.Any, port=1234):
            print("interface.py: Unable to start the server: ", self.tcpServer.errorString())
            return
        ipAddress = getIPAddress()
        print('interface.py: The server is running on', ipAddress, 'port', self.tcpServer.serverPort())

    def readNewMessage(self):
        while self.clients[0].bytesAvailable() >= MESSAGE_LENGTH:
            message = self.clients[0].read(MESSAGE_LENGTH)
            self.newMessage.emit(message)

    def acceptConnection(self):
        newClient = self.tcpServer.nextPendingConnection()
        newClient.readyRead.connect(self.readNewMessage)
        newClient.error.connect(self.controllerConnectionError)
        newClient.disconnected.connect(self.controllerDisconnected)
        self.clients.append(newClient)
        self.newConnection.emit(newClient)

    def acceptError(self, socketError):
        print("interface.py: Server accept error", socketError)

    def controllerConnectionError(self, socketError):
        if socketError == QTcpSocket.RemoteHostClosedError:
            print("interface.py: Client connection closed")
            # print("Client connection closed: ", self.controller.errorString())
        else:
            print("interface.py: TCP client error")
            # print("TCP client error: ", self.controller.errorString())
        print("interface.py: Need to close the socket and remove the the client from the list")

class RobotClient(QObject):
    newMessage = pyqtSignal(tuple)
    def __init__(self, format = "BBBBB"):
        super(RobotClient, self).__init__()
        self.struct = struct.Struct(format)
        self.tcpSocket = QTcpSocket()
        self.tcpSocket.connected.connect(self.connected)
        self.tcpSocket.disconnected.connect(self.disconnected)
        self.tcpSocket.readyRead.connect(self.readNewMessage)
        self.tcpSocket.error.connect(self.displayError)

    def analyzeNewMessage(self, messages):
        for i in range(0, len(messages), len(self.struct.format)):
            message = messages.mid(i, len(self.struct.format))
            decodedMessage = self.struct.unpack(message)
            if sum(decodedMessage)%256 == 0: #checksum valid
                self.newMessage.emit(decodedMessage)
            else:
                print("TCP server checksum failed:", decodedMessage)

    def readNewMessage(self):
        messages = self.tcpSocket.readAll()
        self.analyzeNewMessage(messages=messages)

    def connect(self, ipAddress, port):
        self.tcpSocket.connectToHost(ipAddress, port)
        return self.tcpSocket.waitForConnected(1000)

    def disconnect(self):
        self.tcpSocket.abort()
        self.tcpSocket.close()

    def displayError(self, socketError):
        if socketError == QAbstractSocket.RemoteHostClosedError:
            pass
        elif socketError == QAbstractSocket.HostNotFoundError:
            print("Robot Client:  The host was not found. Please check the host name and port settings.")
        elif socketError == QAbstractSocket.ConnectionRefusedError:
            print("Robot Client: The connection was refused by the peer. Make sure the fortune server is running, and check that the host name and port settings are correct.")
        else:
            print(self, "Robot Client The following error occurred: ", self.tcpSocket.errorString())

    def connected(self):
        print("Connected to server")

    def disconnected(self):
        print("Disconnected from server")

    """"self.write([AUTOMATIC, DISTANCE_TO_BIN, 1, 0])"""
    def write(self, message):
        if self.tcpSocket is not None:
            message.append((256 - sum(message)) % 256)  # checksum
            self.tcpSocket.write(self.struct.pack(*message))
            print("Sent ", str(message))
        else:
            print("Error: trying to send massage ", str(message), "to an None client")

