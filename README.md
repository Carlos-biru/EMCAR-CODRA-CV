# EMCAR  - Embodied Controller for Animating Robots -

Authors:
- Carlos Gomez Cubero @carlos-biru
- Maros Pekarik @marospekarik

This repository contains the tools designed in the HRI lab of Aalborg University to control UR family robots
It forks the following libraries https://github.com/Mandelbr0t/UniversalRobot-Realtime-Control, https://bitbucket.org/RopeRobotics/ur-interface/src https://github.com/robodave94/ur10DrawingSocial

## What is EMCAR?

EMCAR is a set of tools for rapid prototyping, and perform robot interactions. Focused on simplicity and not coding.

It's based on RTDE protocol (real time control for UR). It records the robot movements and drawings and reproduce them in real time.

More info in this publication https://www.frontiersin.org/articles/10.3389/frobt.2021.662249/full

## What do you need?

The repo provide with a set of 3D models for printing under the folder 3D models.
It comes as well with the blender file for quick adjust to your needs.
- Drawing tip
- Corners

You will need a tablet for the drawings. We used Wacom Intuos Pro. Use duct tape around the button of the pen to keep it pressed.

## Robot Setup

Once you have your drawing tip 3D printed measure it's length and create a installation file in the UR teach pendant.
Configure TCP -> Z value to tool length (given model is 140 mm) and Payload ( 0.1kg) 


## Installation
Tested on Python 3.7 and 3.9

```sh
pip3 install opencv-python PyQt5 scipy numpy paho-mqtt six
```

# Run
In App.py change host IP to your robot/simulator IP address, line 51

