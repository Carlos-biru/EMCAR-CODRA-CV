import pyk4a
from pyk4a import PyK4A, Config
import cv2
import numpy as np
import mediapipe as mp
import time
import JsonHandler as auxConf
import CodraCV_Utils as utils


class handDetector():

    def __init__(self):    
        
        # Load camera with the default config
        self.k4a = utils.loadCamera()  # camera object
        self.k4a.start()
        self.perspMatrix = utils.getPerspectiveMatrix()
        
        #self.bg = utils.getImgArr(self.k4a)
        self.bg = cv2.imread("depthBG.png", 0)
        self.time = 0 # used to calculate fps
        
        self.fingers = None
        
    def detectHands(self):
        # RGB img for reference
        img, self.time = utils.addFPS(utils.getImg(self.k4a), self.time)
        cv2.imshow("pic",img)
        # to inprove FPS, we need to pass the capture instead K4a
        
        # Mask FG from depth               
        maskDepth = utils.getFgMask(self.k4a,self.bg)
        depthPers = utils.warpImg(maskDepth, self.perspMatrix)
        #cv2.imshow("pers",maskDepth)               
    
        # Detect Hand,  used masked RGB -> detect fingertips
        masked = cv2.bitwise_and(img , img , mask = maskDepth)
        forHand,fingers = utils.detectHands(masked)
        
        fingersWarp = utils.translFingers2warp(fingers, self.perspMatrix)
        
        warpWFing = utils.printFingersWarp(depthPers, fingersWarp)
        
        forHandWSquare = self.paintSquare(forHand)
        cv2.imshow("Image", forHandWSquare)
        cv2.imshow("warp and fingers",warpWFing)
        
        self.fingers = fingersWarp
            

# Adds a scuare to thru the given points
#
    def paintSquare(self,img):
        conf = auxConf.readJson()
        corn = conf["corners"]
        p1,p2,p3,p4 = corn["TL"] ,corn["BL"] , corn["BR"] , corn["TR"]
        p= (p1,p2,p3,p4)
        points = np.asarray(p)
        for i in range(points.shape[0]):
            cv2.line(img, points[i], points[i-1],(0,255,0), 3)
        for i in range(points.shape[0]):
            cv2.circle(img, points[i],5,(0,0,255),-1)
        return img

if __name__ == '__main__':
    h = None
    h = handDetector()
    while(True):
        h.detectHands()
        k = cv2.waitKey(int(30)) & 0xff
        if k == 27:
            break
    cv2.destroyAllWindows()
    h = None
    
    
    
    