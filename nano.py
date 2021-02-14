""" Jetson Nano side of garntcar """
import sys
import traceback
import time
from time import sleep
from threading import Thread
import serial
from xbox import XBoxController

CONTROLLER_PATH = '/dev/input/event2'

class GarntCar:
    """ Handle car input """
    def __init__(self):
        self.ctrl = XBoxController(CONTROLLER_PATH)
        self.ctrl_thread = Thread(target=self.ctrl.run, args=())
        self.ctrl_thread.daemon = True
        self.ctrl_thread.start()

    def ready(self):
        """ Check if car is ready to drive """
        return self.ctrl.is_started()

    def drive(self):
        """return input values as byte [0-255]"""
        steer = int(self.ctrl.get_steering(low=0, high=255))
        throttle = int(self.ctrl.get_throttle(low=0, high=255))
        return (steer, throttle)

    def stop(self):
        """ Close/release controller """
        self.ctrl.stop()


def main():
    """ Main function """
    serial_port = serial.Serial(
        port="/dev/ttyTHS1",
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )
    time.sleep(1)
    serial_port.flush()
    car = GarntCar()
    serial_port.write(b"n,127,127")
    while not car.ready():
        sleep(0.25)
    serial_port.write(b's')
    do_drive = True
    while do_drive:
        try:
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
    main()
