import URBasic
import numpy as np
import time
import math
import csv
import random
import json
import ContourExtraction
import cv2
import os

#defaultHost = '172.24.210.207'
#defaultHost = '127.0.0.1'
#defaultHost = '169.254.178.76'

#10.0.0.15
#acc = 0.9
#vel = 0.9

class MyRobot(URBasic.urScriptExt.UrScriptExt):
	def __init__(self, host):
		print("Robot connecting to: ", host)
		robotModle = URBasic.robotModel.RobotModel()
		self.robot = URBasic.urScriptExt.UrScriptExt(host=host,robotModel=robotModle)
		self.robot.reset_error()
		self.robot.init_realtime_control()

		#TO DO: SLOW DOWN THIS KILLING MACHINE SOMEHOW
		#self.robot.init_force_remote()
		#self.robot.set_force_remote(limits=[0.05, 0.05, 0.05,0.05, 0.05, 0.05])

		# Speed parameters
		self.a = 0.3
		self.v = 0.3

		 # The parameters of the calibrated canvas
		self.canvasWidth = 0
		self.canvasHeight = 0
		self.canvasMidpoint = 0
		#cropped sizing
		self.canvasCroppedWidth = 0
		self.canvasCroppedHeight = 0
		self.xShift = 0
		self.zHover = 0

		# Save each recorded calibrated point into this class
		with open('calibration_points.json') as json_file:
			points = json.load(json_file)
			self.bottomLeftPoint = points["bottomLeft"]
			self.topLeftPoint = points["topLeft"]
			self.topRightPoint  = points["topRight"]
			self.bottomRightPoint = points["bottomRight"]

		# These parameters represent the variables for translating the alternative values to new coordinates of drawing
		self.theta = 0
		self.Xr = 0
		self.Yr = 0

		self.heightErrorDisplacement = 0

		# The horizontal Planular Equations
		# ax + by + cz + d = 0
		self.plE1_a = 0
		self.plE1_b = 0
		self.plE1_c = 0
		self.plE1_d = 0

		self.ExtraContours = []

		self.zOffset = 0
		self.ep_valP=[0,0]
		self.dist_threshP=[0,0]
		self.endPntPose = [-0.14959202618776724, -0.6892203786569369, 0.45944469344501543,
                           -3.141369099840455, -0.023765232731069934, -0.018604100882098216]
		self.initHoverPos = [0,0,0]

		return

	def constructDrawingCanvas(self):
		p1 = np.array(self.bottomLeftPoint)
		p2 = np.array(self.bottomRightPoint)
		p3 = np.array(self.topLeftPoint)
		# print p1,p2,p3
		v1 = p3 - p1
		v2 = p2 - p1
		cp = np.cross(v1, v2)
		a, b, c = cp
		d = np.dot(cp, p3)
		self.plE1_a = a
		self.plE1_b = b
		self.plE1_c = c
		self.plE1_d = d

		# Display the resulting error margin of the constructed canvas
		testingInputTopRight = self.projectPointToPlane(self.topRightPoint[0], self.topRightPoint[1])
		self.heightErrorDisplacement = testingInputTopRight - self.topRightPoint[2]
		print('Error of ', self.heightErrorDisplacement, ' found')

		# Estimate the canvas width
		bottomWidth = math.sqrt(pow((self.bottomRightPoint[0] - self.bottomLeftPoint[0]) , 2) + pow((self.bottomRightPoint[1] - self.bottomLeftPoint[1]), 2))
		topWidth = math.sqrt(pow((self.topRightPoint[0] - self.topLeftPoint[0]), 2) + pow((self.topRightPoint[1] - self.topLeftPoint[1]), 2))
		self.canvasWidth = (bottomWidth + topWidth) / 2

		# Estimate the canvas height
		leftHeight = math.sqrt(pow((self.topLeftPoint[0] - self.bottomLeftPoint[0]), 2) + pow((self.topLeftPoint[1] - self.bottomLeftPoint[1]), 2))
		rightHeight = math.sqrt(pow((self.topRightPoint[0] - self.bottomRightPoint[0]), 2) + pow((self.topRightPoint[1] - self.bottomRightPoint[1]), 2))
		self.canvasHeight = (leftHeight + rightHeight) / 2

		self.Xr = self.bottomLeftPoint[0]
		self.Yr = self.bottomLeftPoint[1]

		# Find Theta of the canvas
		# In this method we simply calculate the angles from the theta transform to ours
		angA = math.atan2(self.bottomRightPoint[1] - self.bottomLeftPoint[1], self.bottomRightPoint[0] - self.bottomLeftPoint[0])
		angB = math.atan2(self.topRightPoint[1] - self.topLeftPoint[1],
						  self.topRightPoint[0] - self.topLeftPoint[0])
		#angA = math.atan2(self.topLeftPoint[1] - self.bottomLeftPoint[1], self.topLeftPoint[0] - self.bottomLeftPoint[0])
		#angB = math.atan2(self.topRightPoint[1] - self.bottomRightPoint[1],self.topRightPoint[0] - self.bottomRightPoint[0])
		self.theta = (angA + angB) / 2

		# find the canvas midpoint
		# BLTR
		xM1 = (self.bottomLeftPoint[0] + self.topRightPoint[0]) / 2
		yM1 = (self.bottomLeftPoint[1] + self.topRightPoint[1]) / 2

		xM2 = (self.bottomRightPoint[0] + self.topLeftPoint[0]) / 2
		yM2 = (self.bottomRightPoint[1] + self.topLeftPoint[1]) / 2

		self.canvasMidpoint = [(xM1 + xM2) / 2, (yM1 + yM2) / 2]

		#
		Zini = self.projectPointToPlane(self.canvasMidpoint[0], self.canvasMidpoint[1])
		self.initHoverPos = [self.canvasMidpoint[0], self.canvasMidpoint[1], Zini, 2.213345336120183,-2.212550352198813, 0.01]
		return

	def calculateCroppedSizing(self,imgHeight,imgWidth):
		#ratio of height to width of image
		imgRatio = (float)(imgHeight)/imgWidth
		#canvas ratio
		canvasRatio = (float)(self.canvasHeight)/self.canvasWidth
		#when canvas ratio is less than image, we crop the width
		theta = math.atan(imgRatio)
		if canvasRatio<imgRatio:
			self.canvasCroppedHeight = self.canvasHeight
			self.canvasCroppedWidth = self.canvasHeight / math.tan(theta)
			self.xShift = (self.canvasWidth - self.canvasCroppedWidth) / 2
		elif imgRatio>canvasRatio:
			self.canvasCroppedWidth = self.canvasWidth
			self.canvasCroppedHeight = self.canvasWidth * math.tan(theta)
			self.xShift = 0
		else:
			self.canvasCroppedWidth = self.canvasWidth
			self.canvasCroppedHeight = self.canvasHeight
			self.xShift = 0


		print('DIMENSIONS FOR EVALUATION')
		print(f'imgRation: {imgRatio}')
		print(f'canvasRatio: {canvasRatio}')
		print(f'imgD: {imgWidth}, {imgHeight}')
		print(f'canvasD: {self.canvasWidth} {self.canvasHeight}')
		print(f'canvasCroppedWidth: {self.canvasCroppedWidth} canvasCroppedHeight: {self.canvasCroppedHeight}')
		return

	def projectPointToPlane(self,x, y):
		return -(self.plE1_a * x + self.plE1_b * y + self.plE1_d) / self.plE1_c

	def cropPlaneToImage(self):
		return

	def scalePixelsToWorldCoordinates(self,Xi, Yi,imageWidth,imageHeight):
		xS = Xi * (self.canvasCroppedWidth / imageWidth)
		yS = Yi * (self.canvasCroppedHeight / imageHeight)
		return np.array([xS, yS])

	def getTranslatedPositionComponents(self,x, y):
		xS = x+self.xShift
		xR = self.Xr + xS * math.cos(self.theta) - y * math.sin(self.theta)
		yR = self.Yr + y * math.cos(self.theta) + x * math.sin(self.theta)
		return np.array([xR, yR])

	# This code recieves contour points input along the waypoints and converts them to real world systems
	def PixelTranslation(self, xInput, yInput, imageH, imageW):
		'''xS = xInput * (self.canvasWidth / imageWidth)
		yS = yInput * (self.canvasHeight / imageHeight)
		xR = self.Xr + xS * math.cos(self.theta) - yS * math.sin(self.theta)
		yR = self.Yr + yS * math.cos(self.theta) + xS * math.sin(self.theta)
		zR = (-self.plE1_a * xR - self.plE1_b * yR - self.plE1_d) / self.plE1_c
		return [xR,yR,zR]
		'''


		s2 = self.scalePixelsToWorldCoordinates(Xi=xInput, Yi=yInput,imageWidth=imageW,imageHeight=imageH)
		s3 = self.getTranslatedPositionComponents(x=s2[0], y=s2[1])
		return [s3[0], s3[1], self.projectPointToPlane(x=s3[0], y=s3[1])]


	def SetZvals(self, zD, division = 1):
		self.zOffset = zD / division
		self.zHover = self.zOffset + 0.04
		return

	def findIntecepts(self, originpt, horizontalpt, verticalpt):
		# get vertical lines
		pts = [originpt,
			   [originpt[0], verticalpt[1]],
			   [horizontalpt[0], originpt[1]],
			   [horizontalpt[0], verticalpt[1]]]
		return pts

	def setMax_Min(self, btmLft, btmRht, TpLft, TpRht):
		mintercepts = self.findIntecepts([btmLft[0], btmLft[1]], [btmRht[0], btmRht[1]], [TpLft[0], TpLft[1]])
		maxtercepts = self.findIntecepts([TpRht[0], TpRht[1]], [TpLft[0], TpLft[1]], [btmRht[0], btmRht[1]])
		# find the minimum euclidean distance
		minDist = float(50)
		xZero = 0
		yZero = 0
		xMax = 0
		yMax = 0
		for Min in mintercepts:
			for Max in maxtercepts:
				if (minDist > math.sqrt((Max[0] - Min[0]) ** 2 + (Max[1] - Min[1]) ** 2)):
					xZero = Min[0]
					yZero = Min[1]
					xMax = Max[0]
					yMax = Max[1]

		self.SetZvals(float(sum([btmLft[2], btmRht[2], TpLft[2], TpRht[2]]) / 4))

		return xMax, xZero, yMax, yZero

	def midpoint(self, p1, p2):
		return [float((p1[0] + p2[0]) / 2), float((p1[1] + p2[1]) / 2)]

	def PrintAllVar(self):
		print('Bottom Left Point',self.bottomLeftPoint)
		print('Top Left Point',self.topLeftPoint)
		print('Top Right Point',self.topRightPoint)
		print('Bottom Right Point',self.bottomRightPoint)
		print('Theta',self.theta)
		print('Relative X pose',self.Xr)
		print('Relative Y pose',self.Yr)
		print('Canvas Width', self.canvasWidth)
		print('Canvas Height',self.canvasHeight)
		print('Canvas Midpoint',self.canvasMidpoint)
		return

	def getCalibPt(self):
		self.robot.end_freedrive_mode()
		calPt = self.robot.get_actual_tcp_pose()
		print(calPt[0], calPt[1], calPt[2])
		return calPt

	def Calibrate(self, corner, size = [0, 0]):
		if corner == 0:
			calPt = self.getCalibPt()
			self.bottomLeftPoint = [calPt[0], calPt[1], calPt[2], ]
			self.robot.freedrive_mode()
		if corner == 1:
			calPt = self.getCalibPt()
			self.topLeftPoint = [calPt[0], calPt[1], calPt[2], ]
			self.robot.freedrive_mode()
		if corner == 2:
			calPt = self.getCalibPt()
			self.topRightPoint = [calPt[0], calPt[1], calPt[2], ]
			self.robot.freedrive_mode()
		if corner == 3:
			calPt = self.getCalibPt()
			self.bottomRightPoint = [calPt[0], calPt[1], calPt[2], ]
			self.constructDrawingCanvas()
			self.calculateCroppedSizing(size[0], size[1])

			self.PrintAllVar()
			data = {
				"bottomLeft": self.bottomLeftPoint,
				"topLeft": self.topLeftPoint,
				"topRight": self.topRightPoint,
				"bottomRight": self.bottomRightPoint
			}
			with open('calibration_points.json', 'w') as outfile:
				json.dump(data, outfile)
				print("JSON Saved: ", json.dumps(data))

		# setMax_Min(self, self.bottomLeftPoint, self.topLeftPoint, self.topRightPoint, self.bottomRightPoint)
		return

	def RunDrawing(self,image,inputVals=0):
		imgPath = os.path.dirname( __file__ ) + '/drawings/test.jpg'
		image = cv2.imread(imgPath, 0)
		lines = ContourExtraction.JamesContourAlg(image,self.ep_valP[inputVals],self.dist_threshP[inputVals])
		#Crop the image space to match the input image size
		self.calculateCroppedSizing(image.shape[0], image.shape[1])
		line_num = 0
		for q in range(0,len(lines)):
			y = lines[q]
			line_num += 1
			# print(y)
			self.ExtraContours.append(y)
			if len(y)>0:
				#pts = self.convertToTDspaceList(y, [image.shape[0], image.shape[1]])
				pts = []
				for eachPoint in y:
					#print 'point is'
					#print eachPoint
					coords = self.PixelTranslation(eachPoint[0], eachPoint[1], image.shape[0], image.shape[1])
					# print(pts)
					robotCoordFormat = [coords[0],coords[1],-coords[2],self.endPntPose[3],self.endPntPose[4],self.endPntPose[5]]
					pts.append(robotCoordFormat)
					#pts.append([coords[0],coords[1],coords[2],self.endPntPose[3],self.endPntPose[4],self.endPntPose[5]])
				self.DrawContour(pts)
				print("drawing contour")
			self.ExtraContours.remove(y)
		while len(self.ExtraContours)>0:
			print(self.ExtraContours)
			self.DrawContour(self.ExtraContours[0])
			self.ExtraContours.remove(self.ExtraContours[0])
		print ('Completed Contour Construction', line_num)
		#self.rob.movel(self.initHoverPos, acc=self.a, vel=self.v, wait=True)
		return

	def RunDrawingWp(self,image,inputVals=0):
		imgPath = os.path.dirname( __file__ ) + '/drawings/test2.jpg'
		image = cv2.imread(imgPath, 0)
		lines = ContourExtraction.JamesContourAlg(image,self.ep_valP[inputVals],self.dist_threshP[inputVals])
		#Crop the image space to match the input image size
		self.calculateCroppedSizing(image.shape[0], image.shape[1])
		line_num = 0
		dist_tresh = 0.01
		listWpt = []
		prevPoint = [0,0,0]
		for q in range(0,len(lines)):
			y = lines[q]
			line_num += 1
			# print(y)
			self.ExtraContours.append(y)

			if len(y)>0:
				for eachPoint in y:
					if (q%3 == 0):
						coords = self.PixelTranslation(eachPoint[0], eachPoint[1], image.shape[0], image.shape[1])
						dist = math.sqrt((coords[0]-prevPoint[0])**2 + (coords[1]-prevPoint[1])**2)
						if dist > dist_tresh:
							pose = [coords[0],coords[1],-coords[2] + 0.04,self.endPntPose[3],self.endPntPose[4],self.endPntPose[5]]
							robotCoordFormat = {'pose': pose, 'a':1.2, 'v':0.25, 't':0, 'r':0}
							listWpt.append(robotCoordFormat)
						prevPoint = coords
						pose = [coords[0],coords[1],-coords[2],self.endPntPose[3],self.endPntPose[4],self.endPntPose[5]]
						robotCoordFormat = {'pose': pose, 'a':1.2, 'v':0.25, 't':0, 'r':0}

						listWpt.append(robotCoordFormat)

		print(len(self.ExtraContours))
		self.ExecuteWaypointsPath(listWpt)
		#self.rob.movel(self.initHoverPos, acc=self.a, vel=self.v, wait=True)
		return

	def DrawContour(self,pts,validate=False):
		self.ExecuteSinglePath(
			[pts[0][0], pts[0][1], self.zHover, self.endPntPose[3], self.endPntPose[4], self.endPntPose[5]])
		return

	def ExecuteWaypointsPath(self, pt):
		print("Waypoints count:", len(pt))
		self.robot.movel_waypoints(pt)
		return

	def ExecuteSinglePath(self, pt):
		self.robot.movel(pt, a=self.a, v=self.v, wait=False)
		self.DelayWhileExecuting()
		return

	def DelayWhileExecuting(self):
		# time.sleep(0.25)
		# while self.rob.is_program_running() and self.Interruption == False and self.StopCommand == False:
		# 	time.sleep(0.01)
		# if self.Interruption:
		# 	self.InteruptedPosition = self.rob.getl()
		# 	self.rob.stopl(acc=0.8)
		# 	self.RunRetreat()
		# elif self.StopCommand==True:

		return
