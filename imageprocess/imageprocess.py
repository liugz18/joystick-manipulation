#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 03:08:38 2019

@author: ysli
"""

import cv2
import numpy as np
background = cv2.imread('test0.jpg',0)
raw=cv2.imread('test10.jpg',0)
img=abs(raw-background*0.85)
img=img.astype(np.uint8)
clahe = cv2.createCLAHE(clipLimit=7,tileGridSize=(20,20))
img_clahe = clahe.apply(img)
img_blur= cv2.GaussianBlur(img_clahe,(9,9),2)
ret,img_bin = cv2.threshold(img_blur,135,255,cv2.THRESH_BINARY)
circles= cv2.HoughCircles(img_bin,cv2.HOUGH_GRADIENT,1,50,param1=10,param2=8,minRadius=5,maxRadius=30)
result=raw
if not (circles is None):
    for circle in circles[0]:
        x=int(circle[0])
        y=int(circle[1])
        r=int(circle[2])
        result=cv2.circle(raw,(x,y),r,(255,0,0),2)
cv2.imshow('image',result)
cv2.waitKey(0) 
cv2.destroyAllWindows() 
