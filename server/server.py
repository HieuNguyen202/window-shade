#!/usr/bin/python3
from interface import *
from PyQt5.QtCore import QCoreApplication
server = None
nodes = list()


def startListening():
    global server
    server = Server()
    server.newClient.connect(appendNewClient)

def appendNewClient(client):
    global nodes
    node = CLINode(client)
    print("New connection from: ", client.peerAddress().toString(), 'port', client.peerPort())
    nodes.append(node)

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
    app = QCoreApplication(sys.argv)
    startListening()
    app.exec_()