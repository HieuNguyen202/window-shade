#!/usr/bin/python3
from interface import *
from PyQt5.QtCore import QCoreApplication
server = None

def startListening():
    global server
    server = RobotServer()
    server.controllerDisconnected.connect(clientDisconnected)
    server.newConnection.connect(newClient)

def processNewMessage(message):
    print(message)

def clientDisconnected():
    print("A client just disconnected, need to find out which client it is")

def newClient(client):
    print("New connection from: ", client.peerAddress().toString(), 'port', client.peerPort())

if __name__ == '__main__':
    print("Running server.py")
    import sys
    app = QCoreApplication(sys.argv)
    startListening()
    app.exec_()