#!/usr/bin/python3
from interface import *
from graphics import *
from PyQt5.QtCore import QCoreApplication
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
ui = None
server = None
nodes = list()

def startListening():
    global server
    server = Server()
    server.newClient.connect(appendNewClientGUI)

def appendNewClient(client):
    global nodes
    node = CLINode(client)
    print("New connection from: ", client.peerAddress().toString(), 'port', client.peerPort())
    nodes.append(node)
    testCommunication()

def appendNewClientGUI(client):
    global nodes, ui
    node = GUINode(client, ui.appendNode())
    nodes.append(node)

def testCommunication():
    global nodes
    n = nodes[-1]
    n.getPos()
    n.getLight()
    n.getPosMax()
    n.getLightMax()
    n.getPosUpperLimit()
    n.getLightUpperLimit()
    n.getPosLowerLimit()
    n.getLightLowerLimit()
    n.calibrate()
    n.setPos(100)
    n.setLight(200)
    n.setModeSensor(1)
    n.setModeLight(1)

def readNewMessage(self):
    #TODO: create new distributed node Object and give the client object, GUI interface, or command line interface
    while self.clients[0].bytesAvailable() >= MESSAGE_LENGTH:
        message = self.clients[0].read(MESSAGE_LENGTH)
        print(message)

def clientError(self, socketError):
    if socketError == QTcpSocket.RemoteHostClosedError:
        print("interface.py: Client connection closed")
        # print("Client connection closed: ", self.controller.errorString())
    else:
        print("interface.py: TCP client error")
        # print("TCP client error: ", self.controller.errorString())
    print("interface.py: Need to close the socket and remove the the client from the list")

if __name__ == '__main__':
    print("Running server.py")
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    startListening()
    app.exec_()