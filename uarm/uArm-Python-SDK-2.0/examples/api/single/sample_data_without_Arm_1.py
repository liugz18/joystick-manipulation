#coding:utf-8
import os
import sys
import time
import cv2
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI
import pdb
from collections import OrderedDict

def main(video_filename):
    swift = SwiftAPI()
    swift.reset()
    sensor_cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    sensor_cap.set(3, 320)
    sensor_cap.set(4, 240)
    fps = sensor_cap.get(cv2.CAP_PROP_FPS)
    width = sensor_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = sensor_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    sensor_writer = cv2.VideoWriter(video_filename + '.avi',
                                    cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                    30,
                                    (int(width), int(height)))
    count = 0
    while True:
        ret, frame = sensor_cap.read()
        swift.set_position(x=1,speed=1000,relative=True)
        ret = swift.get_servo_angle()
        print('servo angle: {}'.format(ret))
        count += 1
        print(count)
        if ret:
            sensor_writer.write(frame)
            cv2.imshow('sensor data', frame)
        if cv2.waitKey(1) &  0xFF == ord('q'):
            break
        time.sleep(1)
    sensor_cap.release()
    sensor_writer.release()
    swift.reset()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # if len(sys.argv) < 1:
    #     print('Usage: python auto_sample_data.py serial_port [filename(default "sensor")]')
    #     print('Example: python auto_sample_data.py com3 sensor_data')
    #     exit()
    # else:
    #     if len(sys.argv) == 1:
    #         video_filename = 'sensor'
    #     else:
    #         video_filename = sys.argv[1]
    video_filename = 'testtt'
    main(video_filename)