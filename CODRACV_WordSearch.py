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
maxDrawings = 6 
script = ["retreat", "wander", "draw", "draw", "wander", "draw", "draw",
          "wander", "draw", "draw", "retreat"]

roomDrawings = ["WS1","WS2","WS3","WS4","WS5","WS6","WS7","WS8","WS9","WS10",
                "WS11","WS12", "WS13", "WS14", "WS15", "WS16"]
wordsMarked = np.zeros(0)

wordsInRoom1 = [1,2,3,4,5,6,9]
wordsInRoom2 = [7,8]
wordsInRoom3 = [10,11,12,13,14]
wordsInRoom4 = [15,16]
wordsInRoom = [wordsInRoom1,wordsInRoom2,wordsInRoom3,wordsInRoom4]
def interact(i, cond, fingers , R):
    global script
    
    if script[i] == "retreat":
        print("Retreat")
        playAnim(R,"retreat")
    
    elif script[i] == "wander":
        print("Wander")
        #playAnim(R,"wander")
        
    elif script[i] == "draw":
        r = gethandOnRoom(fingers)
        #print(f"Hand on Room {r}")
        if r == -1 :    # Random room
            drawRandRoom(R)
        else:
            if(cond == 1):
                drawCond1(R, r)
            else:
                drawCond2(R,r)


def drawRandRoom(R):
    global wordsMarked
    print("Draw Random")
    if(wordsMarked.size == maxDrawings):
        print("Already max drawings")
        return -1
    word2mark = randint(1,16)        
    while word2mark in wordsMarked:
        print(word2mark)
        word2mark = randint(1,maxDrawings)        

    playDrawing(R,roomDrawings[word2mark-1])
    wordsMarked = np.append(wordsMarked, word2mark)
    
    
def drawCond1(R, handOnRoom):#, redInRoom):
    global wordsMarked
    if(wordsMarked.size == maxDrawings):
        print("Already Max drawings")
        return -1
    print(f"drawCond1 hand on  {handOnRoom}")
    if -1 < handOnRoom <= 4:
        word2mark = randint(1,16)
        # if the word is the words inside the room the hand is over repeat the rand 
        while ((word2mark in wordsMarked) or (word2mark in wordsInRoom[handOnRoom-1])) :
            word2mark = randint(1,16)

    playDrawing(R,roomDrawings[word2mark-1])
    wordsMarked = np.append(wordsMarked, word2mark)
    
    
def drawCond2(R,handOnRoom):#, redInRoom):
    global wordsMarked
    if(wordsMarked.size == maxDrawings): return -1
    
    #Check if there if there is still words in the room where the hand is
    if False not in np.in1d(wordsInRoom[handOnRoom-1],wordsMarked) :
        print(f"Room {handOnRoom} is done already lets go for a random")
        drawRandRoom(R)
    else:
        word2mark = randint(1,16)
        # if the word is in the words inside the room the hand is over 
        while not ((word2mark not in wordsMarked) and  (word2mark in wordsInRoom[handOnRoom-1])) :
            word2mark = randint(1,16)
            
        playDrawing(R,roomDrawings[word2mark-1])
        wordsMarked = np.append(wordsMarked, word2mark)
        
def playDrawing(R, drawing):
    print(f"Play Drawing {drawing}")
    time.sleep(3)
    '''
    R.end_freedrive()
    drawing = R._drawings[drawing]
    result = R.myRobot.playAnimation(drawing)
    print(result)
    '''
def playAnim(R, anim):
    print(f"Play Animation {anim}")
    R.end_freedrive()
    animation = R._animations[anim]
    result = R.myRobot.playAnimation(animation)
    print(result)



def gethandOnRoom(f):
    if checkGoodFingers(f):
        return findRoom(f[1,0],f[1,1])
    else:
        return -1
    
def findRoom(x,y):
    w,h = 1280, 720    
    if x == -1:
        print(f"no room")
        return -1    
    #Divided in 4 rooms, 1->top left, 2->bottom left, 3->top right, 4-> bottom right
    #W divided in 14/30 
    #H divided in 13/21
    room = 1    
    if x > w*(14/30): # right column 
        room += 2
    if y > h*(13/21): # bottom line
        room += 1
    print(f"Hand on Room {room}")
    return room
  
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
            #cv2.imshow("QUEUE",hDet.redLinesImgAVG)

        k = cv2.waitKey(int(30)) & 0xff
        if k == 27:
            cv2.destroyAllWindows()
            endThread = True
            break



cond = 1


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
            #findRoomDraw(img)
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