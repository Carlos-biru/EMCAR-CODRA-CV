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


def threadRobot(name , q):
    app = QApplication(sys.argv)
    R = CODRACVTest.App()
            
    for i in range(600):
        a = q.get()    
        q.put([-1,-1]) #fill the cue so is not updated 
       # print(a)
        if checkGoodFingers(a):
            print(f"INDEX  {posOfIndex(a)}")
            #Translate position to Canvas WS different pix order
            x1, y1 = translateCVPix2Canvas(a[1][0], a[1][1])
            R.drawPointFN(x1,y1)
            #R.drawRTDE(x1,y1)
        else:
            time.sleep(0.2)
        q.get()
    print("-----------bye First Thread--------------------")
    sys.exit(app.exec_())
    
def threadCV(name, q):

    print("Lol")
    hDet= CodraCV_Main.handDetector()
        
    while(True):
        hDet.detectHands()
        #print(hDet.fingers)        
        if checkGoodFingers and q.empty():
            q.put(hDet.fingers)
        
        k = cv2.waitKey(int(30)) & 0xff
        if k == 27:
            cv2.destroyAllWindows()
            endThread = True
            break
 
 
def checkGoodFingers(fingers):
    if fingers[1][0] != -1:
        return True
    else:
        return False
    
def posOfIndex(fingers):
    return fingers[1]       
 
#Add this function to utils
# Open CV count pixels Head down, while Emcar count pixels Botom up
def translateCVPix2Canvas(x,y):
    H = 720
    W = 1280
    return x , H - y
    
    
    
queue = Queue()
thread1 = Thread( target=threadRobot, args=("Thread-1", queue) )
thread2 = Thread( target=threadCV, args=("Thread-2", queue) )

thread1.start()
thread2.start()
thread2.join()
thread1.join()



