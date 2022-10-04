import pyk4a
from pyk4a import PyK4A, Config
import cv2
import numpy as np
import mediapipe as mp
import time
import JsonHandler as auxConf

k4a = None

width, height = 1280,720

# Read config
conf = auxConf.readJson()
corn = conf["corners"]
p1,p2,p3,p4 = corn["TL"] ,corn["BL"] , corn["BR"] , corn["TR"]
p = (p1,p2,p3,p4)
p = np.asarray(p)




# Load the configuration for the kinect
#    
def loadCamera():
    
    return PyK4A(
        Config(
        color_resolution=pyk4a.ColorResolution.RES_1440P,
        #color_resolution=pyk4a.ColorResolution.RES_720P,
        #color_resolution=pyk4a.ColorResolution.RES_2160P,
        
        depth_mode=pyk4a.DepthMode.NFOV_UNBINNED,
        synchronized_images_only=True,

        ))    

# Return the matrix of perspective from the given points
# Order is TL counter clockwise
def getPerspectiveMatrix():
    warpP = np.float32([[0,0] , [0,height] , [width, height],  [width, 0]])
    matrix = cv2.getPerspectiveTransform(np.float32(p),warpP)
    #print(matrix)
    return matrix

# Returns a image
#
def getImg(k4a):
    capture = k4a.get_capture()
    #capture = cv2.resize(capture,(width,height))
    #return capture.depth
    #return capture.transformed_depth
    return cv2.resize(capture.color,(width,height))

# Returns a Image in full resolution 2160
#
def getImgFull(k4a):
    capture = k4a.get_capture()
    return capture.color

# Returns
#

# Returns a depth image U8, each bit is 4mm
# Clip the data between 52cm and 106cm then divide it by 2 ( 255 values)
def getImgArr(k4a):
    img = k4a.get_capture().transformed_depth
    img = cv2.resize(img,(width,height))
    imgClip = np.clip(img, 525, 1065)
    imgComp = (imgClip-525)/2
    imgU8 = imgComp.astype('uint8')
    return imgU8
    
# Opening with a 4x4 kernel
#
def morf(img):
    kernel = np.ones((4,4),np.uint8)
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

    
# Foreground segmentation
#
def getFg(bg, img, th1 = 200, th2 = 2):
        
    difference = bg-img
    difference[difference == 255] = 0
    difference[difference  > th1] = 0 #nsoise
    difference[difference  > th2] = 255

    difference[difference <= th2] = 0
    return difference

# Warp image from points
#
def warpImg(img, matrix):
    return cv2.warpPerspective(img, matrix, (width, height))

# Warp image from a high resolution img
# Map the points to the new resolution and warp the img
def warpImgFull(img):
    h1,w1 = img.shape[0:2]
    p1 = (p*[w1,h1])/[width,height]
    warpP1 = np.float32([[0,0] , [0,h1] , [w1, h1],  [w1, 0]])
    matrix1 = cv2.getPerspectiveTransform(np.float32(p1),warpP1)    
    canvas = cv2.warpPerspective(img, matrix1, (w1, h1))
    return cv2.resize(canvas, (width,height))

# Get foreground over paper
# capture -> arrange -> get fg -> morphology -> mask
def getFgMask(k4a,bg):
    depth       = getImgArr(k4a)
    depthFg     = getFg(bg,depth)     
    mask = morf(depthFg)
    return mask

# Add FPS
# params, img and previous time
def addFPS(img,pTime):
    cTime = time.time()
    #print(f"Ctime = {cTime},   Ptime = {cTime}")
    fps = 1/(cTime-pTime)
    pTime = cTime
    cv2.putText(img,str(int(fps)), (10,70), cv2.FONT_HERSHEY_PLAIN, 3, (255,0,255), 3)
    return img, pTime

# Add a square over the image from the points saved in the config.json
def paintSquare(img):
    #conf = auxConf.readJson()
    #corn = conf["corners"]
    #p1,p2,p3,p4 = corn["TL"] ,corn["BL"] , corn["BR"] , corn["TR"]
    #p= (p1,p2,p3,p4)
    #points = np.asarray(p)
    for i in range(p.shape[0]):
        cv2.line(img, p[i], p[i-1],(0,255,0), 3)
    for i in range(p.shape[0]):
        cv2.circle(img, p [i],5,(0,0,255),-1)
    return img


##############    Hand Detection   #############

mpHands = mp.solutions.hands

hands = mpHands.Hands(static_image_mode=False,
                      max_num_hands=1,
                      min_detection_confidence=0.5,
                      min_tracking_confidence=0.5)

mpDraw = mp.solutions.drawing_utils

# Detect the joint of hands and return the position of finger tips
# https://google.github.io/mediapipe/solutions/hands.html
def detectHands(masked):
    # Hand detection    
    forHand = cv2.cvtColor(masked, cv2.COLOR_BGR2RGB)
    results = hands.process(forHand)
    #print(results.multi_hand_landmarks)
    fingertips = np.zeros((5,2))

    if results.multi_hand_landmarks:
        h, w, c = masked.shape
        for handLms in results.multi_hand_landmarks:
            for id, lm in enumerate(handLms.landmark):
                #print(id,lm)
                cx, cy = int(lm.x *w), int(lm.y*h)
                if id in [4,8,12,16,20]:
                    cv2.circle(forHand, (cx,cy), 4, (int(255/20)*id,255-int(255/20)*id,255), cv2.FILLED)

            #mpDraw.draw_landmarks(forHand, handLms, mpHands.HAND_CONNECTIONS)
    
        for i in range(5):
            fingertips[i][0] = handLms.landmark[(i+1)*4].x * w
            fingertips[i][1] = handLms.landmark[(i+1)*4].y * h

    return forHand , fingertips

# Translate the pixel position in raw image into the warped image
#
def pixRaw2Warp(pX,pY, matrix):
    
    # If the values are -1 is becouse there is no hand    
    if (pX == -1 or pY == -1):
        return [-1,-1]
    # Transformation
    pT = getPixTransf(pX,pY,matrix)
    #print(pT)
    # If is among  
    if(pT[0] > -100 and pT[0] < width+100 and pT[1] > -100 and pT[1] <height+100):
        return np.clip(pT, [0,0], [width,height])
    else:
        return [-1,-1]
    
# Translate the pixels from raw to warp of the pixels
#
def translFingers2warp(fingers, matrix):
    fingersWarp = np.zeros((5,2))
    for i in range(5):
        fingersWarp[i] = pixRaw2Warp(fingers[i,0],fingers[i,1], matrix)   
    return fingersWarp
    
# Print circles from finger values
#
def printFingersWarp(img, fingers):
    for i in range(5):
        cx = int(fingers[i,0])
        cy = int(fingers[i,1])
        #print(f"CX = {cx}  CY = {cy}")
        if(cx > 1 and cy > 1):
            cv2.circle(img, (cx,cy), 8, 100, cv2.FILLED)
    return img

# Apply the same equation that the warpPerspective() fn. 
# https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html
# ---> warpPerspective()
def getPixTransf(x,y,m):
    
    x1 = int((m[0,0]*x + m[0,1]*y + m[0,2]) / (m[2,0]*x + m[2,1]*y + m[2,2]))
    y1 = int((m[1,0]*x + m[1,1]*y + m[1,2]) / (m[2,0]*x + m[2,1]*y + m[2,2]))
    return [x1 , y1]    