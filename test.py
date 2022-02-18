#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys
import traceback

import numpy as np
from PIL import Image
from threading import Thread


from camera import CSICamera

def main():

    data_dir = f'{os.getcwd()}/data/{time.strftime("%m_%d_%Y/%H_%M_%S")}'
    image_dir = f'{data_dir}/images'
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)


    cam = CSICamera(image_w=1280, image_h=720, image_d=3, capture_width=1280, capture_height=720, framerate=60, gstreamer_flip=0)
    cam_thread = Thread(target=self.cam.run, args=())
    cam_thread.daemon = True
    cam_thread.start()

    # Pi Camera
    # camera = CSICamera(image_w=1280, image_h=720, image_d=3, capture_width=1280, capture_height=720, framerate=60, gstreamer_flip=0)

    print('recording')

    recording = True
    while recording:
        try:
            image = cam.poll_camera()
            image_path = f'{image_dir}/{time.time()}.png'
            image.save(image_path)

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
