#!/usr/bin/python3
from interface import *
from PyQt5.QtCore import QCoreApplication

robot = None

def connect():
    global robot
    robot = RobotClient()
    robot.tcpSocket.connected.connect(robotConnected)
    robot.tcpSocket.disconnected.connect(robotDisconnected)
    if not robot.connect("104.194.104.162", port=1234):
        robot.tcpSocket.connected.disconnect()
        robot.tcpSocket.disconnected.disconnect()

def robotConnected():
    print("client.py: Connected to server")

def robotDisconnected():
    print("client.py: Disconnected from server")

if __name__ == '__main__':
    print("Running client.py")
    import sys
    app = QCoreApplication(sys.argv)
    connect()
    app.exec_()