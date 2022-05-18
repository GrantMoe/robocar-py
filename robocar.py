import os
import serial
import time
import io


def main(conf):

    steering_in = None
    throttle_in = None
    switch_in = None
    input_needed = True
    input_requested = False

    # set up paths for data recording
    data_dir = f'{os.getcwd()}/data/{time.strftime("%m_%d_%Y/%H_%M_%S")}'
    os.makedirs(data_dir, exist_ok=True)

    # pyserial.readthedocs.io/en/latest/shortintro.html
    ser = serial.Serial('/dev/ttyACM0', timeout=1)

    while True:


        if input_needed and not input_requested:
            ser.write(b'g')
            input_requested = True

        if ser.in_waiting > 0:
            line = str(ser.readline())
            print(f'serial line: {line}')

            if line[0] == 'i':
                inputs = line[1:].split(',')
                steering_in = inputs[0]
                throttle_in = inputs[1]
                switch_in = inputs[2]


    # # start serial with Teensy
    # serial_port = serial.Serial(
    #     port=conf['serial_port'],
    #     baudrate=115200,
    #     bytesize=serial.EIGHTBITS,
    #     parity=serial.PARITY_NONE,
    #     stopbits=serial.STOPBITS_ONE,
    # )
    # time.sleep(1)
    # serial_port.flush()

    # initialize gpsd input

    # set up NTRIP stream?

    
    # get input from Teensy via serial
    # output_string = f"i"
    # print(output_string)
    # serial_port.write(output_string.encode())
    

    # process drive mode
    # process drive status
    # get GPS data
    # afs
     