#coding:utf-8
import sys
import time
import cv2
import numpy as np
from grblcmd import GrblCmd
import pdb
from collections import OrderedDict

#def main(serial_port, video_filename):
def main( video_filename):
    # servo_com = GrblCmd(serial_port)
    # servo_com.spindle_up()
    # time.sleep(3)
    # servo_com.spindle_down()
    # time.sleep(3)
    sensor_cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    sensor_cap.set(3, 320)
    sensor_cap.set(4, 240)
    fps = sensor_cap.get(cv2.CAP_PROP_FPS)
    width = sensor_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = sensor_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    sensor_writer = cv2.VideoWriter(video_filename + '.avi',
                                    cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                    30,(int(width), int(height)))
    count = 0
    while True:
        ret, frame = sensor_cap.read()
        #servo_com.move_x(1)
        count += 1
        print(count)
        if ret:
            sensor_writer.write(frame)
            cv2.imshow('sensor da'
                       'ta', frame)
        if cv2.waitKey(1) &  0xFF == ord('q'):
            break
        time.sleep(0.1)
    sensor_cap.release()
    sensor_writer.release()
    # servo_com.spindle_down()
    # time.sleep(2)
    # servo_com.spindle_up()
    # time.sleep(2)
    # servo_com.go_home()
    # time.sleep(3)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # if len(sys.argv) < 2:
    #     print('Usage: python auto_sample_data.py serial_port [filename(default "sensor")]')
    #     print('Example: python auto_sample_data.py com3 sensor_data')
    #     exit()
    # else:
    #     serial_port = sys.argv[1]
    #     if len(sys.argv) == 2:
    #         video_filename = 'sensor'
    #     else:
    #         video_filename = sys.argv[2]
    video_filename = 'testt1'
    #main(serial_port, video_filename)
    main(video_filename)