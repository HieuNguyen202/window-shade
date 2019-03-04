from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket, QNetworkInterface, QAbstractSocket
from PyQt5.QtCore import pyqtSignal, QObject
MESSAGE_LENGTH = 5  #Including checksum

def getIPAddress():
    for ipAddress in QNetworkInterface.allAddresses():
        if ipAddress != QHostAddress.LocalHost and ipAddress.toIPv4Address() != 0:
            break
    else:
        ipAddress = QHostAddress(QHostAddress.LocalHost)
    return ipAddress.toString()

class Server(QTcpServer):
    newConnection = pyqtSignal(QTcpSocket)
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
        self.newConnection.emit(self.nextPendingConnection())

    def acceptErrorHandler(self, socketError):
        print("interface.py: Server accept error", socketError)

class GUI(QObject):
    pass

class CLI(QObject):
    pass

class Node(QObject):
    pass