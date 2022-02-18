""" Jetson Nano side of garntcar """
import argparse
from email.mime import image
import sys
import traceback
import time
from time import sleep
from threading import Thread
import serial
import os

import numpy as np
from PIL import Image

import config
from xbox import XBoxController
from tx import BleGamePad
from camera import CSICamera


class GarntCar:
    """ Handle car input """
    def __init__(self, conf):
        if conf['controller_type'] == 'xbox':
            self.ctrl = XBoxController(conf['controller_path'])
        elif conf['controller_type'] == 'ble_gamepad':
            self.ctrl = BleGamePad(conf['controller_path'])
        self.ctrl_thread = Thread(target=self.ctrl.run, args=())
        self.ctrl_thread.daemon = True
        self.ctrl_thread.start()

    def ready(self):
        """ Check if car is ready to drive """
        return self.ctrl.is_started()

    def drive(self):
        """return input values as byte [0-255]"""
        steer = 127
        throttle = 127
        if self.ready():
            steer = int(self.ctrl.get_steering(low=0, high=255))
            throttle = int(self.ctrl.get_throttle(low=0, high=255))
        return (steer, throttle)

    def stop(self):
        """ Close/release controller """
        self.ctrl.stop()

class NanoCam:

    def __init__(self, image_dir):
        self.cam = CSICamera()
        self.cam_thread = Thread(target=self.cam.run, args=())
        self.cam_thread.daemon = True
        self.cam_thread.start()
        self.image_dir = image_dir

    def save_frame(self):
        image = self.cam.poll_camera()
        image_path = f'{self.image_dir}/{time.time()}.png'
        image.save(image_path)
            

def main(conf):
    """ Main function """

    # set up path for telemetry/video
    data_dir = f'{os.getcwd()}/data/{time.strftime("%m_%d_%Y/%H_%M_%S")}'
    image_dir = f'{data_dir}/images'
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    # Pi Camera
    camera = NanoCam(image_dir)

    # serial connection to the Teensy
    serial_port = serial.Serial(
        port=conf['serial_port'],
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )
    time.sleep(1)
    serial_port.flush()
    car = GarntCar(conf)
    serial_port.write(b"n,127,127")
    while not car.ready():
        sleep(0.25)
    serial_port.write(b's')
    do_drive = True

    while do_drive:
        try:
            camera.save_frame()
            serial_port.flush()
            steer_byte, throttle_byte = car.drive()
            output_string = f"n,{steer_byte},{throttle_byte}"
            print(output_string)
            serial_port.write(output_string.encode())
            sleep(0.1)

        except KeyboardInterrupt:
            do_drive = False
        except Exception as exception_error:
            print("Error occurred. Exiting Program")
            print("Error: " + str(exception_error))
            traceback.print_exc(file=sys.stdout)

    car.stop()
    serial_port.write('x'.encode())
    serial_port.flush()
    serial_port.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="robocar")
    parser.add_argument("--controller_type",
                        type=str,
                        default="xbox",
                        help="controller type",
                        choices=config.default_controller_type)
    parser.add_argument("--controller_path",
                        type=str,
                        default=config.default_controller_path,
                        help="path to input event controller device")
    parser.add_argument("--serial_port",
                        type=str,
                        default=config.default_serial_port,
                        help="dev/tty* port for microcontroller",
                        )
    # parser.add_argument("--records_directory",
    #                     type=str,
    #                     default=f"{os.getcwd()}/data"
    #                     help="folder for telemetry/images")
    # add vehicle type? camera path, whether to record etc. ?
    args = parser.parse_args()
    conf = {
        'controller_type': args.controller_type,
        'controller_path': args.controller_path,
        'serial_port': args.serial_port,
    }
    main(conf)
