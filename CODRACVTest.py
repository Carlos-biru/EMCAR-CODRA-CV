import sys, traceback
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import json
import time
import scipy.interpolate
import math
import operator
import os
import random 

# import URBasic
# from MqttClient import MqttClient
from Robot import MyRobot
from Worker import Worker, WorkerSignals
from TabletWindow import WindowDraw
from Utils import figureOrientation

animationssss = None
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("RoboApp", "App")

        
        self.wWidth = 1200#1200
        self.wHeight = 860#720#1080#860
        self.canvasW = 1280#1280#self.settings.value("width") or 1920 #2560
        self.canvasH = 720#self.settings.value("height") or 1080 #1440

        
        with open('./data/animations.json') as json_file:
        			anims = json.load(json_file)
        			self._animations = anims
        global animationssss
        
        
        with open('./data/drawings.json') as json_file:
            f = json.load(json_file) 
            self._drawings = f

        
		#self.myRobot = False
        self.activated = False
        self.freeModeOn = False

        self.selectedAnimIndex = 0
        self.selectedFileIndex = 0
        self.selectedDrawIndex = 0

        self.isRecording = False
        self.isRecordingTablet = False
        self.isAnimationPlaying = False
        self.isHovering = False

        self.threadpool = QThreadPool()
        #self.window_draw = WindowDraw(self,app)

        animationssss = anims
        self.myRobot = MyRobot(app = self, host = '192.168.1.100')
        self.myRobot.SetZvals(float(self.settings.value("z_offset") or 0), division=100) #0.04)

        self.myRobot.constructDrawingCanvas()
        self.myRobot.calculateCroppedSizing(self.canvasH, self.canvasW)

        self.isAnimationPlaying = True

        #worker = Worker(self.playAnim) # Any other args, kwargs are passed to the run function
        #worker.signals.result.connect(self.print_play_output)
        #worker.signals.progress.connect(self.progress_fn)

		# Execute
        #self.threadpool.start(worker)

         #worker = Worker(self.drawToPoint) # Any other args, kwargs are passed to the run function
         #worker.signals.result.connect(self.print_play_output)
         #worker.signals.progress.connect(self.progress_fn)

		# Execute
         #self.threadpool.start(worker)
        
        self.xHand = 0
        self.yHand = 0

        
        self.show()


    def playAnim(self, progress_callback):
        self.end_freedrive()
        #animation = self._animations[self.selectedAnimText]
        animation = self._animations["no"]
        result = self.myRobot.playAnimation(animation)
        print(result)

    def progress_fn(self, pose):
        print(pose)

    def end_freedrive(self):
        self.myRobot.robot.end_freedrive_mode()
        #self.buttons["free_mode"].setStyleSheet("background-color : lightgrey")
        self.freeModeOn = False

    def print_play_output(self, s):
		#self.manageAnimButtons(enable=True)
        self.isAnimationPlaying = False
        
    def closeEvent(self, event):
        print ("User has clicked the red x on the main window")
        self.myRobot.robot.robotConnector.RTDE.close()
        event.accept()


        
        
    def drawToPoint(self,progress_callback):
        x = self.xHand
        y = self.yHand
        penDown = 100
        for i in range(5):
            x = x+i*10
            y = y+i*5
            print(f"{x}  {y}   {self.canvasH}     {self.canvasW}")
            coord = self.myRobot.PixelTranslation(x, y, self.canvasH, self.canvasW)
            print(coord)
            z = -coord[2] + self.myRobot.zOffset
            if penDown < 15:
                z = -coord[2] + 0.04                
            self.myRobot.robot.set_realtime_pose([coord[0], coord[1], z, 0,3.14,0])
            time.sleep(2)

    def drawPointFN(self,x,y):
        penDown = 0
        coord = self.myRobot.PixelTranslation(x, y, self.canvasH, self.canvasW)
        z = -coord[2] + self.myRobot.zOffset
        if penDown < 15:
            z = -coord[2] + 0.04                
        #self.myRobot.robot.set_realtime_pose([coord[0], coord[1], z, 0,3.14,0])
        pt = [coord[0], coord[1], z, 0,3.14,0]
        self.myRobot.ExecuteSingleLinear(pt , a = 0.2 , v = 0.4)
        print("Reached possition")
        
    def drawRTDE(self, x, y):
        penDown = 0
        coord = self.myRobot.PixelTranslation(x, y, self.canvasH, self.canvasW)
        z = -coord[2] + self.myRobot.zOffset
        if penDown < 15:
            z = -coord[2] + 0.04                
        self.myRobot.robot.set_realtime_pose([coord[0], coord[1], z, 0,3.14,0])
        #pt = [coord[0], coord[1], z, 0,3.14,0]
        #self.myRobot.ExecuteSingleLinear(pt , a = 0.2 , v = 0.4)
        print("Reached possition")
        
    def main():
        app = QApplication(sys.argv)
        a = App()
        print("by bye--------")
        sys.exit(app.exec_())
        print("bye bye you you")   



if __name__ == '__main__':
    print("Whats up broouu!!!")
    #main()

