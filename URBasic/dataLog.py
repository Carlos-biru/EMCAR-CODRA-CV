'''
Python 3.x library to control an UR robot through its TCP/IP interfaces
Copyright (C) 2016  Martin Huus Bjerge, Rope Robotics ApS, Denmark

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software 
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies 
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL "Rope Robotics ApS" BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Except as contained in this notice, the name of "Rope Robotics ApS" shall not be used 
in advertising or otherwise to promote the sale, use or other dealings in this Software 
without prior written authorization from "Rope Robotics ApS".
'''
__author__ = "Martin Huus Bjerge"
__copyright__ = "Copyright 2016, Rope Robotics ApS, Denmark"
__license__ = "MIT License"

import threading
import URBasic
import numpy as np
import time



class DataLog(threading.Thread):
    '''
    This module handle logging of all data signal from the robot (not event logging).
    ''' 
    def __init__(self, robotModel):

        if(False):
            assert isinstance(robotModel, URBasic.robotModel.RobotModel)  ### This line is to get code completion for RobotModel
        self.__robotModel = robotModel
        threading.Thread.__init__(self)
        logger = URBasic.dataLogging.DataLogging()
        name = logger.AddDataLogging(__name__)
        self.__dataLogger = logger.__dict__[name]
        name = logger.AddEventLogging(__name__,log2Consol=True)        
        self.__logger = logger.__dict__[name]
        self.__stop_event = True

        self.__robotModelDataDirCopy = None
        self.start()
        self.__logger.info('DataLog constructor done')
         
    def logdata(self, robotModelDataDir):
        if(self.__robotModelDataDirCopy != None):
            if(self.__robotModelDataDirCopy['timestamp'] != robotModelDataDir['timestamp']):
                for tagname in robotModelDataDir.keys():
                    if tagname != 'timestamp' and  robotModelDataDir[tagname] is not None:
                        tp = type(robotModelDataDir[tagname])
                        if tp is np.ndarray:
                            if 6==len(robotModelDataDir[tagname]):
                                self.__dataLogger.info((tagname+';%s;%s;%s;%s;%s;%s;%s'), robotModelDataDir['timestamp'], *robotModelDataDir[tagname])
                            elif 3==len(robotModelDataDir[tagname]):
                                self.__dataLogger.info((tagname+';%s;%s;%s;%s'), robotModelDataDir['timestamp'], *robotModelDataDir[tagname])
                            else:
                                self.__logger.warning('Logger data unexpected type in rtde.py - class URRTDElogger - def logdata Type: ' + str(tp) + ' - Len: ' + str(len(robotModelDataDir[tagname])))
                        elif tp is bool or tp is float or tp is int: 
                            self.__dataLogger.info((tagname+';%s;%s'), robotModelDataDir['timestamp'], robotModelDataDir[tagname])
                        else:
                            self.__logger.warning('Logger data unexpected type in rtde.py - class URRTDElogger - def logdata Type: ' + str(tp))
        self.__robotModelDataDirCopy = robotModelDataDir
        
                    
    def close(self):
        if self.__stop_event is False:
            self.__stop_event = True
            self.join()
 
    def run(self):
        self.__stop_event = False
        while not self.__stop_event:
            try:
                temp = self.__robotModel.dataDir.copy()
                self.logdata(temp)
                time.sleep(0.005)
            except:
                self.__logger.warning("DataLog error while running, but will retry")
        self.__logger.info("DataLog is stopped")
