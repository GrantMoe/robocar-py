#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys
import traceback

import numpy as np
from PIL import Image
from threading import Thread

class CSICamera():
    '''
    Camera for Jetson Nano IMX219 based camera
    Credit: https://github.com/feicccccccc/donkeycar/blob/dev/donkeycar/parts/camera.py
    gstreamer init string from https://github.com/NVIDIA-AI-IOT/jetbot/blob/master/jetbot/camera.py
    '''
    def gstreamer_pipeline(self, capture_width=3280, capture_height=2464, output_width=224, output_height=224, framerate=21, flip_method=0) :   
        return 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=%d, height=%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv flip-method=%d ! nvvidconv ! video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! videoconvert ! appsink' % (
                capture_width, capture_height, framerate, flip_method, output_width, output_height)
    
    def __init__(self, image_w=1280, image_h=720, image_d=3, capture_width=1280, capture_height=720, framerate=60, gstreamer_flip=0):
        '''
        gstreamer_flip = 0 - no flip
        gstreamer_flip = 1 - rotate CCW 90
        gstreamer_flip = 2 - flip vertically
        gstreamer_flip = 3 - rotate CW 90
        '''
        self.w = image_w
        self.h = image_h
        self.running = True
        self.frame = None
        self.flip_method = gstreamer_flip
        self.capture_width = capture_width
        self.capture_height = capture_height
        self.framerate = framerate

    def init_camera(self):

        # initialize the camera and stream
        self.camera = cv2.VideoCapture(
            self.gstreamer_pipeline(
                capture_width =self.capture_width,
                capture_height =self.capture_height,
                output_width=self.w,
                output_height=self.h,
                framerate=self.framerate,
                flip_method=self.flip_method),
            cv2.CAP_GSTREAMER)

        self.poll_camera()
        print('CSICamera loaded.. .warming camera')
        time.sleep(2)

    def poll_camera(self):
        self.ret , frame = self.camera.read()
        print(self.ret)
        if self.ret:
            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.frame

def main():

    data_dir = f'{os.getcwd()}/data/{time.strftime("%m_%d_%Y/%H_%M_%S")}'
    image_dir = f'{data_dir}/images'
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)


    cam = CSICamera(image_w=1280, image_h=720, image_d=3, capture_width=1280, capture_height=720, framerate=60, gstreamer_flip=0)
    cam.init_camera()
    # cam_thread = Thread(target=cam.run, args=())
    # cam_thread.daemon = True
    # cam_thread.start()

    # Pi Camera
    # camera = CSICamera(image_w=1280, image_h=720, image_d=3, capture_width=1280, capture_height=720, framerate=60, gstreamer_flip=0)

    print('recording')

    recording = True
    while recording:
        try:
            image = cam.poll_camera()
            # print('polled camera')
            if image:
                print('image if')
                image_path = f'{image_dir}/{time.time()}.png'
                cv2.imwrite(image_path, image)
                # image.save(image_path)
        except KeyboardInterrupt:
            recording = False
        except Exception as exception_error:
            print("Error occurred. Exiting Program")
            print("Error: " + str(exception_error))
            traceback.print_exc(file=sys.stdout)
        
    cam.shutdown()

    print('done')

if __name__ == "__main__":
    main()
