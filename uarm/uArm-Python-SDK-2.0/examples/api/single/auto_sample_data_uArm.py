#coding:utf-8
import os
import sys
import time
import cv2
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI
import pdb
import io
from collections import OrderedDict
import serial
#port = '/dev/ttyACM1'
port = 'COM19'
bps = 115200
timex = 1
ser = serial.Serial(port, bps, timeout=timex)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

def parse_radio_data(data_string):
    """parse the radio data which is in format 
        like 'c1:1000 c2:1023 c3:1033 c4:1972"""
    result = []
    for data in data_string.split():
        result.append(float(data.split(':')[1]))
    return result
def main(video_filename):
    swift = SwiftAPI()
    swift.reset()
    swift.set_position(z=75,speed=1000)
    sensor_cap = cv2.VideoCapture(1)
    sensor_cap.set(3, 320)
    sensor_cap.set(4, 240)
    width = sensor_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = sensor_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    sensor_writer = cv2.VideoWriter(video_filename + '.avi',
                                    cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                    30,
                                    (int(width), int(height)))
    count = 0
    mode=1
    while True:
        ret, frame = sensor_cap.read()
        swift.set_position(x=0.6*mode,speed=200,relative=True)
        pos=swift.get_position()
        print(pos)
        count += 1
        print(count)
        if ret:

            ret, thresh = cv2.threshold(cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY), 127, 255, cv2.THRESH_BINARY)
            # findContours函数查找图像里的图形轮廓
            # 函数参数thresh是图像对象
            # 层次类型，参数cv2.RETR_EXTERNAL是获取最外层轮廓，cv2.RETR_TREE是获取轮廓的整体结构
            # 轮廓逼近方法
            # 输出的返回值，image是原图像、contours是图像的轮廓、hier是层次类型
            image, contours, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(frame, contours, -1, (255, 0, 0), 2)

            sensor_writer.write(frame)
            cv2.imshow('sensor data', frame)
            sio.write("s")
            sio.flush()
            data = sio.readline()
            print('raw data:', data)
#            data = parse_radio_data(data)
#            print('joystick data:',data)
        if cv2.waitKey(1) &  0xFF == ord('q'):
            break
        time.sleep(0.2)
        if count==100:
            mode=(-1)*mode
            count=0
    sensor_cap.release()
    sensor_writer.release()    
    cv2.destroyAllWindows()
    swift.reset()

if __name__ == '__main__':
    main('3sensor')