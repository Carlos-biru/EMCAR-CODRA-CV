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
import numpy as np
from random import randint


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
            #R.drawPointFN(x1,y1)
            R.drawRTDE(x1,y1)
        else:
            time.sleep(0.2)
        q.get()
    print("-----------bye First Thread--------------------")
    sys.exit(app.exec_())
    
def threadCV(name, q):

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
    #print(f"chechGoodFingers {fingers}")
    if fingers[0][0] != -1:
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
    

def getHandOnRoom(f):
    if checkGoodFingers(f):
        return findRoom(f[1,0],f[1,1])
    else:
        return -1
    
def findRoom(x,y):
    #(16,11.5)  (30,12)
    #(16,17)    (30,18.5)     
    #pixels per cm in A3 with 1280x720, A3 = 42x30cm
    w,h = 1280, 720
    pixW = w/42
    pixH = h/30
    
    if x == -1:
        return -1
    
    #Room 4  center  
    if pixW*16 < x < pixW*30 :
        return 4
    #Rooms 1,2,3
    elif pixW*16 > x:
        if pixH*11.5 > y:
            return 1
        if pixH*17 > y:
            return 2
        else:
            return 3
    #Rooms
    elif x > pixW*30:
        if pixH*12 > y:
            return 5
        if pixH*18.5 > y:
            return 6
        else:
            return 7
    
#13 steps
i = 0
maxIter = 13
script = ["retreat", "wander", "room", "room", "wander", "room", "room",
          "wander", "room", "room", "wander", "room", "retreat"]

roomDrawings = ["BP1","BP2","BP3","BP4","BP5","BP6","BP7"]
roomsPainted = np.zeros(1)

# i = iteration;  cond = condition;  fingers = f data; R = robot
#   
def interact(i, cond, fingers , R):
    global script
    
    if script[i] == "retreat":
        print("Retreat")
        playAnim(R,"retreat")
    
    elif script[i] == "wander":
        print("Wander")
        #playAnim(R,"wander")
        
    elif script[i] == "room":
        r = getHandOnRoom(fingers)
        print(f"Room {r}")
        if r == -1 :    # Random room
            drawRandRoom(R)
        else:
            if(cond == 1):
                drawCond1(R, r)
            else:
                drawCond2(R,r)
        

def drawRandRoom(R):
    global roomsPainted
    print("Draw Random")
    if(roomsPainted.size == 7): return -1
    room = randint(1,7)        
    while room in roomsPainted:
        print(room)
        room = randint(1,7)        

    playDrawing(R,roomDrawings[room-1])
    roomsPainted = np.append(roomsPainted, room)
    
def drawCond1(R, HandOnRoom):
    global roomsPainted
    if(roomsPainted.size == 7): return -1
    
    if -1 < HandOnRoom <= 3:
        if false in np.in1d(roomsPainted, [4,5,6,7]):
            drawRandRoom(R)
            return 0
        else:            
            room = randint(4,7)
            while (room in roomsPainted) :
                room = randint(4,7)
        
    if HandOnRoom > 4:
        if false in np.in1d(roomsPainted, [1,2,3,4]):
            drawRandRoom(R)
            return 0
        else:
            room = randint(1,4)
            while (room in roomsPainted) :
                room = randint(1,4)
    if HandOnRoom == 4:
        if not(false in np.in1d(roomsPainted, [1,2,3,5,6,7])):
            room = 4
        else:
            room = randint(1,7)
            while(room ==  4 or room in roomsPainted):
                room = rand(1,7)

    playDrawing(R,roomDrawings[room-1])
    roomsPainted = np.append(roomsPainted, room)
    
def drawCond2(R,HandOnRoom):
    global roomsPainted
    if(roomsPainted.size == 7): return -1
    
    if HandOnRoom in roomsPainted :
        drawRandRoom(R)
    else:   
        playDrawing(R,roomDrawings[HandOnRoom-1])
        roomsPainted = np.append(roomsPainted, HandOnRoom)
        
def playDrawing(R, drawing):
    print(f"Play Drawing {drawing}")
    
    R.end_freedrive()
    drawing = R._drawings[drawing]
    result = R.myRobot.playAnimation(drawing)
    print(result)
    
def playAnim(R, anim):
    print(f"Play Animation {anim}")
    R.end_freedrive()
    animation = R._animations[anim]
    result = R.myRobot.playAnimation(animation)
    print(result)

cond = 2

if __name__ == '__main__':
    
    queue = Queue()
    thread1 = Thread( target=threadCV, args=("Thread-CV", queue) )
    thread1.start()
    
    app = QApplication(sys.argv)
    R = CODRACVTest.App()

    #clear buffer
    queue.get(timeout = 1) # finger data
    time.sleep(0.5)
    f = queue.get(timeout = 1)


    while thread1.is_alive() and i < maxIter:#4:
        try:
            queue.get(timeout = 1) # finger data
            time.sleep(0.5)
            f = queue.get(timeout = 1)
            queue.put([-1,-1]) #fill the cue so is not updated
            print(f"Index position {f[1]}")
        except Empty as error:
            break
        interact(i, cond, f, R)

        time.sleep(0.2)
        queue.get()
        i+=1
    print("cerramos o qui???")
    time.sleep(1)
    R.close()
    sys.exit()




