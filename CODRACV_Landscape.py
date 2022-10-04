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


i = 2
maxIter = 11
script = ["retreat", "wander", "draw", "draw", "wander", "draw", "draw",
          "wander", "draw", "draw", "retreat"]

roomDrawings = ["SP1","SP2","SP3","SP4","SP5","SP6","SP7","SP8,",
                "SP9","SP10","SP11","SP12"]
roomsPainted = np.zeros(1)
cond = 2

def interact(i, cond, fingers , R):
    global script
    
    if script[i] == "retreat":
        print("Retreat")
        #playAnim(R,"retreat")
    
    elif script[i] == "wander":
        print("Wander")
        #playAnim(R,"wander")
        
    elif script[i] == "draw":
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
    
def drawCond1(R, HandOnRoom):#, redInRoom):
    global roomsPainted
    if(roomsPainted.size == 7): return -1
    
    if -1 < HandOnRoom <= 12:
        if np.in1d(roomsPainted, [4,5,6,7]):
            drawRandRoom(R)
            return 0
        else:            
            room = randint(4,7)
            while (room in roomsPainted) :
                room = randint(4,7)
        
    if HandOnRoom > 4:
        if np.in1d(roomsPainted, [1,2,3,4]):
            drawRandRoom(R)
            return 0
        else:
            room = randint(1,4)
            while (room in roomsPainted) :
                room = randint(1,4)
    if HandOnRoom == 4:
        if np.in1d(roomsPainted, [1,2,3,5,6,7]):
            room = 4
        else:
            room = randint(1,7)
            while(room ==  4 or room in roomsPainted):
                room = rand(1,7)

    playDrawing(R,roomDrawings[room-1])
    roomsPainted = np.append(roomsPainted, room)
    
def drawCond2(R,HandOnRoom):#, redInRoom):
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











def getHandOnRoom(f):
    if checkGoodFingers(f):
        return findRoom(f[1,0],f[1,1])
    else:
        return -1
    
def findRoom(x,y):
    w,h = 1280, 720    
    if x == -1:
        print(f"no room")
        return -1
    
    #W divided in 4
    #H divided in 3
    roomXPos = 0
    roomYPos = 0
    for dw in range(4):
        if  x < w*(dw+1)/4:
            roomXPos = dw
            break
    for dh in range(3):
        if y < h*(dh+1)/3:
            roomYPos = dh
            break
    print(f"Room is {roomYPos*4 + roomXPos + 1}")
    return roomYPos*4 + roomXPos + 1
  
def findRoomDraw(img):
    h1,w1 = img.shape
    redInRooms = np.zeros(0)
    print(img.shape)
    for dh in range(3):
        for dw in range(4):
            roomI = img[int(h1*dh/3):int(h1*(dh+1)/3), int(w1*(dw)/4):int(w1*(dw+1)/4)]
            if int(np.sum(roomI)/255) > 800:
                redInRooms = np.append(redInRooms, dh*4 + dw  +1)
                print(f" Room {dh*4 + dw  +1} pixels = {int(np.sum(roomI)/255)}" )

def checkGoodFingers(fingers):
    #print(f"chechGoodFingers {fingers}")
    if fingers[0][0] != -1:
        return True
    else:
        return False
    
def posOfIndex(fingers):
    return fingers[1]       
 

def threadCV(name, q,qImg):

    hDet= CodraCV_Main.handDetector()
        
    while(True):
        hDet.detectHands()
        #print(hDet.fingers)        
        if checkGoodFingers and q.empty():
            q.put(hDet.fingers)

        hDet.detectDrawing()
        
        if qImg.empty():
            qImg.put(hDet.redLinesImgAVG)
            cv2.imshow("QUEUE",hDet.redLinesImgAVG)

        k = cv2.waitKey(int(30)) & 0xff
        if k == 27:
            cv2.destroyAllWindows()
            endThread = True
            break





if __name__ == '__main__':
    
    queue = Queue()
    queueImg = Queue()
    thread1 = Thread( target=threadCV, args=("Thread-CV", queue, queueImg) )
    thread1.start()
    
    app = QApplication(sys.argv)
    R = CODRACVTest.App()

    #clear buffer
    queue.get(timeout = 1000) # finger data
    
    time.sleep(0.5)
    f = queue.get(timeout = 1000)

    while thread1.is_alive() and i < maxIter:#4:
        try:
            queue.get(timeout = 1) # finger data
            time.sleep(0.5)
            f = queue.get(timeout = 1000)
            img = queueImg.get(timeout = 1000)
            queue.put([-1,-1]) #fill the cue so is not updated
            print(f"Index position {f[1]}")
            findRoomDraw(img)
        except Exception as error:
            print(traceback.format_exc())
            break
        #R=None
        interact(i, cond, f, R)

        time.sleep(0.2)
        queue.get()
        queueImg.get()
        i+=1
    print("cerramos o qui???")
    time.sleep(1)
    R.close()
    sys.exit()
