import traceback
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
        #main resolution
        self.w = utils.width
        self.h = utils.height
        
        # Load camera with the default config
        self.k4a = utils.loadCamera()  # camera object
        self.k4a.start()
        # Get perspective matrix
        self.perspMatrix = utils.getPerspectiveMatrix()
        # Load Image to average the red lines
        self.redLinesImgAVG = np.zeros((self.h,self.w), np.uint8)
        self.bg = cv2.imread("depthBG.png", 0)
        self.time = 0 # used to calculate fps
        
        self.fingers = None

    # Updates the finger position in the fingers variable adjusted to the
    # warped image
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
        
        forHandWSquare = utils.paintSquare(forHand)
        cv2.imshow("Image", forHandWSquare)
        cv2.imshow("warp and fingers",warpWFing)
        
        self.fingers = fingersWarp
        
    def detectDrawing(self):
        
        # Get color img + HSV
        img = utils.getImgFull(self.k4a)
        imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Get canvas color img (HSV)
        canvasHSV = cv2.resize(utils.warpImgFull(imgHSV),(self.w,self.h))
        # Get red drawing
        self.getRedColorWithDepthMask(canvasHSV)
        cv2.imshow("HSV",canvasHSV)
        cv2.imshow("AVG", self.redLinesImgAVG)
    
    # Extract the red lines from a given image
    # Expect a HSV input
    def getRedColor(self,img):
        redLow1  = np.array([0,20,20], np.uint8)
        redHigh1 = np.array([8,255,255],np.uint8)
        redLow2  = np.array([150,20,20], np.uint8) 
        redHigh2 = np.array([179,255,255],np.uint8)        
        
        maskR1 = cv2.inRange(img,redLow1,redHigh1)
        maskR2 = cv2.inRange(img,redLow2,redHigh2)
        maskRed = cv2.add(maskR1,maskR2)
        return maskRed
    
    # Extract the red line taking in account the FG mask ( Hand, robot..)
    # Expect a HSV input
    def getRedColorWithDepthMask(self,img):
         # Get canvas Mask FG from depth           
        maskDepth = utils.getFgMask(self.k4a,self.bg)
        depthPers = utils.warpImg(maskDepth, self.perspMatrix)
        depthPers = cv2.dilate(depthPers,np.ones((40, 40), np.uint8), iterations = 1)
        # Get red drawing
        colorMask = self.getRedColor(img)
        FGmaskNot = cv2.bitwise_not(depthPers)
        redLinesWithMask = cv2.bitwise_and(colorMask,colorMask,mask = FGmaskNot)
        # update the avgImage
        self.avgRedLines(redLinesWithMask,depthPers,FGmaskNot)
        return redLinesWithMask
    
    # Average the red lines, uses the depth background to mask the average
    #
    def avgRedLines(self, img, mask, maskNot):
        avgPreMask   = cv2.addWeighted(img, 0.2, self.redLinesImgAVG,0.8,0.0)
        avgMinusMask = cv2.bitwise_and(avgPreMask,avgPreMask,mask = maskNot)
        avgHidenUnder= cv2.bitwise_and(self.redLinesImgAVG,self.redLinesImgAVG,mask = mask)
        
        self.redLinesImgAVG = avgMinusMask + avgHidenUnder
    
if __name__ == '__main__':
    try:
        h = None
        h = handDetector()
        while(True):
            h.detectHands()
            h.detectDrawing()
            k = cv2.waitKey(int(30)) & 0xff
            if k == 27:
                break
        cv2.destroyAllWindows()
    except Exception:    
        print(traceback.format_exc())

        h = None
    
    
    
    