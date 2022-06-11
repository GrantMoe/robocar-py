import os
import serial
import sys
import time
import traceback

from serial.threaded import LineReader, ReaderThread
from threading import Thread

# pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.threaded.ReaderThread
class MicroControllerSerial(LineReader):
    def connection_made(self, transport):
        super(MicroControllerSerial, self).connection_made(transport)
        sys.stdout.write('port opened\n')
        self.write_line('hello world')

    def handle_line(self, data):
        decoded_data = data.strip()
        channels = list(map(int, decoded_data.split(',')))
        for i, channel in enumerate(channels):
            print(f"{i+1}: {channel}", end = " ")
        print()
        self.write_line('foo!')

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        sys.stdout.write('port closed\n')


def main():

    # set up paths for data recording
#    data_dir = f'{os.getcwd()}/data/{time.strftime("%m_%d_%Y/%H_%M_%S")}'
#    os.makedirs(data_dir, exist_ok=True)

    # start serial with Teensy
    ser = serial.Serial(
        # port='/dev/ttyACM0', # Desk/Laptop
        port='/dev/ttyTHS1', # Jetson Nano
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )

    new_thread = ReaderThread(ser, MicroControllerSerial)
    new_thread.start()
    time.sleep(2)
    new_thread.stop()

if __name__ == "__main__":
    main()
