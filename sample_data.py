#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 17:59:38 2019

@author: ysli
"""
import random
import cv2
import serial
import io
from uarm.wrapper import SwiftAPI
import pickle
from collections import deque
import math
import numpy as np
def randompos():
    x=random.randint(-20,20)
    y=random.randint(-20,20)
    return[x,y]
    
def setsensor(video_filename):
    sensor_cap = cv2.VideoCapture(0)
    sensor_cap.set(3, 320)
    sensor_cap.set(4, 240)
    width = sensor_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = sensor_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    sensor_writer = cv2.VideoWriter(video_filename + '.avi',
                                    cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                    30,
                                    (int(width), int(height)))
    return sensor_cap,sensor_writer

def setjoystick():
    port = '/dev/ttyACM1'
    bps = 115200
    timex = 1
    ser = serial.Serial(port, bps, timeout=timex)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
    return sio

def setuarm():
    swift = SwiftAPI()
    swift.reset()
    return swift

def getbgimg(sensor_cap):
    ret,bg=sensor_cap.read()
    return bg

def readjoystick(sio):
    sio.write("s")
    sio.flush()
    data_string = sio.readline()
    result=[]
    for data in data_string.split():
        splitdata=data.split(':')
        if(splitdata[1].strip()==''):
            return [-1,-1,-1,-1] #invalid signal
        else:
            result.append(float(splitdata[1]))
    return result
def readdata(sensor_cap,sio,swift,data,rank):
    ret, img=sensor_cap.read()
    joystickpos=readjoystick(sio)
    armpos=swift.get_position()
    armpolar=swift.get_polar()
    data.append((rank,img,joystickpos,armpos,armpolar))
    cv2.imshow('sensor data', img)
    
def writedata(data):
    fw=open("data.p", "wb")
    print('saving data')    
    pickle.dump(data,fw)
    
print('initializing')  
sensor_cap,sensor_writer=setsensor('0sensor')
sio=setjoystick()
swift=setuarm()
bg=getbgimg(sensor_cap)
data=deque()
rank=[0,0]
swift.set_position(z=75,speed=1000)
print('collection starts')
while(True):
    pos=randompos()
    waypointnum=math.ceil((pos[0]**2+pos[1]**2)**0.5)
    waypoints=np.zeros((2,waypointnum))
    waypoints[0]=np.linspace(0,pos[0],waypointnum,endpoint=True)
    waypoints[1]=np.linspace(0,pos[1],waypointnum,endpoint=True)
    waypoints=np.transpos(waypoints)
    rank[1]=0
    for waypoint in waypoints:
        swift.set_position(x=waypoint[0],y=waypoint[1],speed=200)#if doesn't work, use raletive position
        readdata(sensor_cap,sio,swift,data,rank)
        rank[1]+=1
    if cv2.waitKey(1) &  0xFF == ord('q'):
        break
    rank[0]+=1  

writedata(data)