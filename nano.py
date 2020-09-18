from time import sleep
from threading import Thread
import time
from xbox import XBoxController


CONTROLLER_PATH = '/dev/input/event2'


class GarntCar:

    def __init__(self):
        self.ctrl = XBoxController(CONTROLLER_PATH)
        self.nav = {'steering': 0, 'throttle': 0}
        self.ctrl_thread = Thread(target=self.ctrl.run, args=())
        self.ctrl_thread.daemon = True
        self.ctrl_thread.start()


    def drive(self):
        self.nav['steering'] = self.ctrl.get_steering()
        self.nav['throttle'] = self.ctrl.get_throttle()
        return self.nav



def main():

    car = GarntCar()
    do_drive = True
    while do_drive:
        try:
            car.drive()
            print(car.nav)
            time.sleep(0.1)
        except KeyboardInterrupt:
            do_drive = False



if __name__ == "__main__":
    main()