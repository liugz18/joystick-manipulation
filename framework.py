#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 17:16:34 2019

@author: ysli
"""
#directions 1:up, 2:down, 3:left, 4:right
#actions: up(0,15),down(0,-15),left(-15,0),right(15,0)
def target():
    command=input("target direction:")
    if(command=='w'):
        direction=1
    elif(command=='s'):
        direction=2
    elif(command=='a'):
        direction=3
    elif(command=='d'):
        direction=4
    else:
        print("invalid direction")
    return direction

def targetimg(currentimg,direction):
    