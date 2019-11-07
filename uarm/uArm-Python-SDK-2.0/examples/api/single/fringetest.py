import time
import cv2
import numpy as np


def main(video_filename):
    #sensor_cap = cv2.VideoCapture('3sensor.avi')
    sensor_cap = cv2.VideoCapture(0)

    if cv2.VideoCapture. isOpened:
        print('successfully open video file!!')
    sensor_cap.set(3, 320)
    sensor_cap.set(4, 240)
    width = sensor_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = sensor_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    sensor_writer = cv2.VideoWriter(video_filename + '.avi',
                                    cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                    30,
                                    (int(width), int(height)))

    while True:
        ret, frame = sensor_cap.read()
        if ret:
            ret, thresh = cv2.threshold(cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY), 156, 255, cv2.THRESH_BINARY)
            # findContours函数查找图像里的图形轮廓
            # 函数参数thresh是图像对象
            # 层次类型，参数cv2.RETR_EXTERNAL是获取最外层轮廓，cv2.RETR_TREE是获取轮廓的整体结构
            # 轮廓逼近方法
            # 输出的返回值，image是原图像、contours是图像的轮廓、hier是层次类型
            contours, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(frame, contours, -1, (255, 0, 0), 2)
            '''print(len(contours))
            if len(contours) > 1:
                c = contours[0]

                (x  , y), radius = cv2.minEnclosingCircle(c)
                # 规范化为整数
                center = (int(x), int(y))
                radius = int(radius)
                # 勾画圆形区域
                img = cv2.circle(frame, center, radius, (0, 255, 0), 2)
'''
            sensor_writer.write(frame)
            cv2.imshow('sensor data', thresh)
            #cv2.imshow('sensor data', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        time.sleep(0.2)

    sensor_cap.release()
    sensor_writer.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main('6sensor')