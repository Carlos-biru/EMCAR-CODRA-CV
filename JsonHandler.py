# -*- coding: utf-8 -*-
"""
Example of Json,
To lern how to use it :)
"""

import json


file = "config.json"

#Initialize the JSON to default
def initJson():
    configJson = {
        
        "corners":{
            "TL" : [355,320],
            "BL" : [368, 563],
            "BR" : [703,528],
            "TR" : [684,305]
            }    
        }
    saveJson(configJson)

#Save the Json from String to file
def saveJson(strJson):
    
    jsonString = json.dumps(strJson, indent=4)
    jsonFile = open(file, "w")
    jsonFile.write(jsonString)
    jsonFile.close()

#Read the JSON file to a dictionary
def readJson():
    f = open(file)
    conf = json.load(f)
    #print(json.dumps(conf, indent=2))
    return conf

#initJson()
#readJson()

