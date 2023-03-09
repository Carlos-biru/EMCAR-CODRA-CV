import sys, traceback
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import CODRACVTest
import CodraCV_Main
from threading import Thread 
from queue import Queue
import time
import cv2

app = QApplication(sys.argv)
R = CODRACVTest.App()

for i in range(100):
            
#    time.sleep()
    #a = R.myRobot.robot.robot.get_tcp_force()
    #b = R.myRobot.robot.force()
 
   #while(R.myRobot.robot.robotConnector.RobotModel.ActualTCPForce() is None):      ## check paa om vi er startet
   #         print("waiting for everything to be ready")


    print(R.myRobot.get_actual_tcp_pose())

    #print(R.myRobot.get_tcp_force())