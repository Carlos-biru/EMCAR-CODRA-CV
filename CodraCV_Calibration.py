import pyk4a
from pyk4a import PyK4A, Config
import cv2
import numpy as np
import mediapipe as mp
import time
import JsonHandler as auxConf      # own script to handle JSON
import CodraCV_Utils as utils

# Load camera with the default config
k4a = PyK4A(
        Config(
        color_resolution=pyk4a.ColorResolution.RES_720P,
        #color_resolution=pyk4a.ColorResolution.RES_2160P,
        depth_mode=pyk4a.DepthMode.NFOV_UNBINNED,
        synchronized_images_only=True,
        ))
k4a.start()

# Read config
conf = auxConf.readJson()
corn = conf["corners"]
p1,p2,p3,p4 = corn["TL"] ,corn["BL"] , corn["BR"] , corn["TR"]
p= (p1,p2,p3,p4)
p = np.asarray(p)

width, height = 1280,720       #default res of the canvas
mouseX,mouseY = 0,0         #position of mouse in image

newP = np.zeros((4,2), dtype = int)

depthBgImg = cv2.imread("depthBG.png")

def updateConfigCorners():
    global newP
    global conf
    conf["corners"]["TL"] = int(newP[0][0]) , int(newP[0][1])
    conf["corners"]["BL"] = int(newP[1][0]) , int(newP[1][1])
    conf["corners"]["BR"] = int(newP[2][0]) , int(newP[2][1])
    conf["corners"]["TR"] = int(newP[3][0]) , int(newP[3][1])

    auxConf.saveJson(conf)

# Store the values of the corners when clicking
#
def findXY_callback(event, x, y, flags, params):
    global i
    global newP
    if event == cv2.EVENT_LBUTTONDBLCLK:
        #print(f"coords {x, y}, value{capture.color[y,x]}   params: {params}")    
        newP[i] = [x,y]
        i+=1
    global mouseX
    global mouseY
        
    mouseX = x
    mouseY = y
        
# Adds a looking glass to the left corner of the image
# Inputs, Image, x and y of mouse position
def addLookingGlass(img, x, y):
    if(x > 6 and y > 6):
        lookingGlass = cv2.resize(img[y-5:y+5,x-5:x+5], (100,100),
                                  interpolation =cv2.INTER_NEAREST)
        cv2.rectangle(lookingGlass,(40,40),(60,60),(255,0,0),2)
        img[-101:-1 ,-101:-1 ] = lookingGlass
        print(f"X,Y = {x} - {y}")
    return img

# Adds a scuare to thru the given points
#
def paintSquare(img, points):
    
    for i in range(points.shape[0]):
        cv2.line(img, points[i], points[i-1],(0,255,0), 3)
    for i in range(points.shape[0]):
        cv2.circle(img, points[i],5,(0,0,255),-1)
    return img

# Tells the distance to the center of the picture
#
def getDistance2(bgImg):
    median = np.median(bgImg)    
    center = bgImg[int(bgImg.shape[0]/2), int(bgImg.shape[1]/2)]
    #print(f"median = {median}")
    #print(f"center = {center}")
    return median, center
       

# Function to run the calibration of the canvas
# Allow to click on the image and then save the points
#
i = 0
def caliibrateCanvas():
    global i
    global p
    global newP
    i = 0
    msg = ["Corner Top Left","Corner Boton Left","Corner Bottom Right","Corner Top Right"]    

    # Window to click on corners    
    cv2.destroyAllWindows()
    cv2.namedWindow("SetCorners")
    cv2.setMouseCallback("SetCorners", findXY_callback)    
    while(i < 4):
        capture = k4a.get_capture()
        rawImg = cv2.cvtColor(capture.color, cv2.COLOR_BGRA2BGR)
        cv2.putText(rawImg,msg[i], (0,100), cv2.FONT_HERSHEY_PLAIN, 4, (0,255,0), 3)
        cv2.imshow("SetCorners",addLookingGlass(rawImg,mouseX,mouseY))
            
        k = cv2.waitKey(300) & 0xff
        if k == 27:
            cv2.destroyAllWindows()
            break

    # Window to accept the config
    warpP = np.float32([[0,0] , [0,height] , [width, height],  [width, 0]])
    matrix = cv2.getPerspectiveTransform(np.float32(newP),warpP)
    msgRedo = "Press: ","S to accept","R to redo", "ESC to cancel"
    while(1):
    
        canvasImg = cv2.warpPerspective(rawImg, matrix, (width, height),flags=cv2.INTER_NEAREST) 
        cv2.putText(canvasImg,msgRedo[0], (50,100), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)
        cv2.putText(canvasImg,msgRedo[1], (50,150), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)
        cv2.putText(canvasImg,msgRedo[2], (50,200), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)
        cv2.putText(canvasImg,msgRedo[3], (50,250), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)

        cv2.imshow("Result",canvasImg)
    
        k = cv2.waitKey(300) & 0xff
        if k == 27:
            cv2.destroyAllWindows()
            break
        if k == ord('s'):
            cv2.destroyAllWindows()
            updateConfigCorners()
            p = newP
            break

# Function to save the depth background
# Apply the function "img arrange" and save it in the file depthBG.png
#


def calibrateDepthBG():
    global k4a
    msg = "ESC cancel" , "S save bg"
    while(1):
        depth = utils.getImgArr(k4a)
        depth_text = depth.copy()        
        cv2.putText(depth_text,msg[0], (50,100), cv2.FONT_HERSHEY_PLAIN, 3, (255), 3)
        cv2.putText(depth_text,msg[1], (50,150), cv2.FONT_HERSHEY_PLAIN, 3, (255), 3)

        cv2.imshow(" depthImage" , depth_text)
        
        k = cv2.waitKey(300) & 0xff
        if k == 27:
            cv2.destroyAllWindows()
            break
        if k == ord('s'):
            cv2.destroyAllWindows()
            cv2.imwrite("depthBG.png", depth)            
            break


def menu():        
    global p
    msg = "Calibration!!", "C for Canvas", "B for background "  ,"ESC to leave"
    
    cv2.destroyAllWindows()
    cv2.namedWindow("MenuCalibration")
    while(1):
        capture = k4a.get_capture()
        rawImg = cv2.cvtColor(capture.color, cv2.COLOR_BGRA2BGR)
        med, dist = getDistance2(capture.transformed_depth)
        strDist = f"Distance {dist} mm"                
        cv2.putText(rawImg,msg[0], (0,100), cv2.FONT_HERSHEY_PLAIN, 3, (255,255,255), 7)
        cv2.putText(rawImg,msg[1], (0,150), cv2.FONT_HERSHEY_PLAIN, 3, (255,255,255), 7)
        cv2.putText(rawImg,msg[2], (0,200), cv2.FONT_HERSHEY_PLAIN, 3, (255,255,255), 7)
        cv2.putText(rawImg,msg[3], (0,250), cv2.FONT_HERSHEY_PLAIN, 3, (255,255,255), 7)
        cv2.putText(rawImg,strDist, (0,300), cv2.FONT_HERSHEY_PLAIN, 3, (255,255,255), 7)

        cv2.putText(rawImg,msg[0], (0,100), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)
        cv2.putText(rawImg,msg[1], (0,150), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)
        cv2.putText(rawImg,msg[2], (0,200), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)
        cv2.putText(rawImg,msg[3], (0,250), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)
        cv2.putText(rawImg,strDist, (0,300), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,0), 3)


        withSquare = paintSquare(rawImg, p)
        cv2.imshow("MenuCalibration",withSquare)
        
        
        k = cv2.waitKey(300) & 0xff
        if k == 27:
            cv2.destroyAllWindows()
            return "Q"
        if k == ord('c'):
            cv2.destroyAllWindows()
            return "C"
        if k == ord('b'):
            cv2.destroyAllWindows()
            return "B"
        

if __name__ == "__main__":
   
    op = "m"
    
    while(op != "Q"):
        op = menu()
        
        if op == "C":
            caliibrateCanvas()
        if op == "B":
           calibrateDepthBG() 

#add close the K4a


import sys
sys.exit("Bye Bye")
