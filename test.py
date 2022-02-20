#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys
import traceback
import cv2

#import numpy as np
#from PIL import Image
#from threading import Thread


def gstreamer_pipeline(capture_width=1280, capture_height=720, output_width=1280, output_height=720, framerate=60, flip_method=0) :   
    return 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=%d, height=%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv flip-method=%d ! nvvidconv ! video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! videoconvert ! appsink' % (
                capture_width, capture_height, framerate, flip_method, output_width, output_height)
    

def main():

    data_dir = f'{os.getcwd()}/data/{time.strftime("%m_%d_%Y/%H_%M_%S")}'
    image_dir = f'{data_dir}/images'
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)


    cam = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
#    ret, image = cam.read()
#    cv2.imwrite('test.png', image)

    print('recording')

    recording = True
    while recording:
        try:
            ret, frame = cam.read()
            # print('polled camera')
            if ret:
                print('image if')
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image_path = f'{image_dir}/{time.time()}.png'
                cv2.imwrite(image_path, image)
                # image.save(image_path)
        except KeyboardInterrupt:
            recording = False
        except Exception as exception_error:
            print("Error occurred. Exiting Program")
            print("Error: " + str(exception_error))
            traceback.print_exc(file=sys.stdout)


    print('done')

if __name__ == "__main__":
    main()
