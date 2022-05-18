import os
import serial
import time
import io


def main():

    steering_in = None
    throttle_in = None
    switch_in = None
    input_needed = True
    input_requested = False

    # set up paths for data recording
    data_dir = f'{os.getcwd()}/data/{time.strftime("%m_%d_%Y/%H_%M_%S")}'
    os.makedirs(data_dir, exist_ok=True)

    # pyserial.readthedocs.io/en/latest/shortintro.html
    #ser = serial.Serial('/dev/ttyTHS1', timeout=1)

    # start serial with Teensy
    serial_port = serial.Serial(
        port='/dev/ttyTHS1',
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )
    time.sleep(1)
    serial_port.flush()

    print('setup complete')

    serial_port.write(b's')

    while True:
        print(f'{input_requested = }, {input_needed = }')

        if input_needed and not input_requested:
            serial_port.write(b'g')
            input_requested = True

        if serial_port.in_waiting > 0:
            bytes_in = serial_port.readline()
            print(f'{bytes_in = }')            
            line = str(bytes_in)
            print(f'serial line: {line}')
            inputs = line[1:].split(',')
            print(f'{inputs = }')

            if line[0] == 'i':
                #inputs = line[1:].split(',')
                steering_in = inputs[0]
                throttle_in = inputs[1]
                switch_in = inputs[2]
                input_needed = True
                input_requested = False

        time.sleep(1)


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

if __name__ == "__main__":
    main()
