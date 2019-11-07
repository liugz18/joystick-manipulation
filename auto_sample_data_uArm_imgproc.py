#coding:utf-8
import sys
import time
import cv2
import numpy as np
from uarm.wrapper import SwiftAPI
import pdb
import io
from collections import OrderedDict
import serial
port = '/dev/ttyACM1'
bps = 115200
timex = 1
#ser = serial.Serial(port, bps, timeout=timex)
#sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

def parse_radio_data(data_string):
    """parse the radio data which is in format 
        like 'c1:1000 c2:1023 c3:1033 c4:1972"""
    result = []
    for data in data_string.split():
        result.append(float(data.split(':')[1]))
    return result
def imageprocess(img):
    background = cv2.imread('test0.jpg',0)
    raw=cv2.imread('test4.jpg',0)
    img=abs(raw-background*0.85)
    img=img.astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=7,tileGridSize=(20,20))
    img_clahe = clahe.apply(img)
    #img_clahe = clahe.apply(img_clahe)
    img_blur= cv2.GaussianBlur(img_clahe,(9,9),2)
    ret,img_bin = cv2.threshold(img_blur,120,255,cv2.THRESH_BINARY)
    circles= cv2.HoughCircles(img_bin,cv2.HOUGH_GRADIENT,1,30,param1=10,param2=8,minRadius=10,maxRadius=30)
if not (circles is None):
    for circle in circles[0]:
        x=int(circle[0])
        y=int(circle[1])
        r=int(circle[2])
        result=cv2.circle(raw,(x,y),r,(255,0,0),2)
def main(video_filename):
#    swift = SwiftAPI()
#    swift.reset()
#    swift.set_position(z=75,speed=1000)
    sensor_cap = cv2.VideoCapture(0)
    sensor_cap.set(3, 320)
    sensor_cap.set(4, 240)
    width = sensor_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = sensor_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    sensor_writer = cv2.VideoWriter(video_filename + '.avi',
                                    cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                    30,
                                    (int(width), int(height)))
    result_writer = cv2.VideoWriter(result + '.avi',
                                    cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                    30,
                                    (int(width), int(height)))
    count = 0
    mode=1
    while True:
        ret, frame = sensor_cap.read()
#        swift.set_position(x=0.3*mode,speed=200,relative=True)
#        pos=swift.get_position()
#        print(pos)
        count += 1
        print(count)
        if ret:
            sensor_writer.write(frame)
            cv2.imshow('sensor data', frame)
            '''
            sio.write("s")
            sio.flush()
            data = sio.readline()
            print('raw data:', data)
#            data = parse_radio_data(data)
#            print('joystick data:',data)
            '''
        if cv2.waitKey(1) &  0xFF == ord('q'):
            break
        time.sleep(1)
        if count==100:
            mode=(-1)*mode;
            count=0
    sensor_cap.release()
    sensor_writer.release()    
    cv2.destroyAllWindows()
#    swift.reset()

if __name__ == '__main__':
    main('0sensor')