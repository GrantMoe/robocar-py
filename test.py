#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import asyncio
import serial
import time
from enum import Enum
from bleak import BleakClient

# Adafruit nrf58320
addr = "EF:EB:FD:C7:F8:DA"

DATA = None

# Default Adafruit BleUUART for now
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# PWM_MIN = 1000
# PWM_MAX = 2000
STEERING_NEUTRAL = 127
THROTTLE_NEUTRAL = 127
TRAIN_MIN = 170
AUTO_MAX = 85

# for bit masks, etc.
class Button(Enum):
    JOY_UP  = 0
    JOY_DOWN = 1
    JOY_LEFT = 2
    JOY_RIGHT = 3
    JOY_SELECT = 4
    TFT_A = 5
    TFT_B = 6
    CH_4 = 7

class Drive_Mode(Enum):
    AUTO = 0
    DATA = 1
    MANUAL = 2

class Menu_Mode(Enum):
    AUTO = 0
    DATA = 1
    ERASE = 2
    MANUAL = 3
    PAUSED = 4

class Recorder:

    def __init__(self):
        self.recording = False
        self.erasing = False
        self.records = 0
        self.seconds_to_erase = 0

    def erase_records(self):
        pass

    def record_data(self):
        pass

class Transmitter:
  
    STR = 127
    THR = 127
    TOG = 127
    BTNS = 0

    def __init__(self):
        self.drive_mode = Drive_Mode.MANUAL
        self.menu_mode = None
        self.auto_throttle = False
        self.auto_driving = False
        self.started = False

    def update(self, data):
        print('tx.update')
        # parse BLE bytearray
        data_list = data.split(b',')
        if len(data_list) >= 3:
            self.STR = data_list[0][0]
            self.THR = data_list[1][0]
            self.TOG = data_list[2][0]
            self.BTNS = data_list[3][0]
        # start/stop switch
        if self.is_pressed(Button.CH_4):
            self.started = True
        else:
            self.started = False
        # drive mode
        if self.TOG > TRAIN_MIN:
            self.drive_mode = Drive_Mode.DATA
        elif self.TOG < AUTO_MAX:
            self.drive_mode = Drive_Mode.AUTO
        else:
            self.drive_mode = Drive_Mode.MANUAL


    def is_pressed(self, btn):
        return self.BTNS & 1 << btn.value

    def manual_drive(self):
        return self.STR, self.THR

    def auto_drive(self):
        if self.auto_throttle:
            return STEERING_NEUTRAL, THROTTLE_NEUTRAL
        else:
            return STEERING_NEUTRAL, self.THR

    def drive(self):
        if self.auto_driving:
            if self.drive_mode == Drive_Mode.AUTO:
                return self.auto_drive()
            else:
                return self.manual_drive()
        return STEERING_NEUTRAL, THROTTLE_NEUTRAL

# def byte_to_pwm(in_byte):
#     pwm = ( (in_byte - 0) / (256 - 0) ) * (2000 - 1000) + 1000
#     return pwm

async def run_control_task(input_queue: asyncio.Queue, 
    output_queue: asyncio.Queue, serial_port: serial.Serial):
    global DATA
    print('starting run control')

    tx = Transmitter()
    rec = Recorder()

    steering_out = STEERING_NEUTRAL
    throttle_out = THROTTLE_NEUTRAL

    while True:
        data = DATA
        #print('waiting for input data')
        #data = await input_queue.get()
        #print('got data')
        if data == None:
            print('no data!')
            await asyncio.sleep(0.5)
            continue

        tx.update(data)

        # process inputs
        if tx.started:
            if tx.drive_mode == Drive_Mode.AUTO:
                tx.menu_mode = Menu_Mode.AUTO
                # toggle auto throttle
                if tx.is_pressed(Button.TFT_A):
                    if tx.auto_throttle:
                        tx.auto_throttle = False
                    else:
                        tx.auto_throttle = True
                if tx.is_pressed(Button.TFT_B):
                    if tx.auto_driving:
                        tx.auto_driving = False
                    else:
                        tx.auto_driving = True
            elif tx.drive_mode == Drive_Mode.DATA:
                if rec.erasing:
                    tx.menu_mode = Menu_Mode.ERASE
                    # confirm erasure
                    if tx.is_pressed(Button.TFT_B):
                        rec.erase_records()
                        rec.erasing = False
                    # cancel erasure
                    elif tx.is_pressed(Button.TFT_A):
                        rec.seconds_to_erase = 0
                        rec.erasing = False
                    # add seconds
                    elif tx.is_pressed(Button.JOY_UP):
                        rec.seconds_to_erase += 5
                    # remove seconds
                    elif tx.is_pressed(Button.JOY_DOWN):
                        rec.seconds_to_erase -= 5
                        rec.seconds_to_erase = min(rec.seconds_to_erase, 0)
                else:
                    tx.menu_mode = Menu_Mode.DATA
                    rec.record_data()
                    # toggle recording
                    if tx.is_pressed(Button.TFT_B):
                        if rec.recording:
                            rec.recording = False
                        else: 
                            rec.recording = True
                    # activate erase mode
                    elif tx.is_pressed(Button.TFT_A):
                        rec.recording = False
                        rec.erasing = True
            else: # tx.drive_mode = Drive_Mode.MANUAL
                tx.menu_mode = Menu_Mode.MANUAL
        else:
            tx.menu_mode = Menu_Mode.PAUSED

        print('main section compelete')

        # get outputs
        steering_out, throttle_out = tx.drive()

        # Send controls to Teensy
        serial_port.flush()
        output_string = f"n,{steering_out},{throttle_out}" 
        serial_port.write(output_string.encode())
        print('controls sent to teensy')


        menu_fields = ''
        if tx.menu_mode == Menu_Mode.AUTO: 
            menu_fields = f'a,{int(tx.auto_driving)},{int(tx.auto_throttle)}'
        elif tx.menu_mode == Menu_Mode.DATA:
            menu_fields = f'd,{int(rec.recording)},{rec.records}'
        elif tx.menu_mode == Menu_Mode.ERASE:
            menu_fields = f'e,{rec.seconds_to_erase}'
        elif tx.menu_mode == Menu_Mode.MANUAL:
            menu_fields = 'm'

        msg = bytearray(menu_fields, 'utf-8')

        await output_queue.put(msg)

        # Print controls
        os.system('clear')
        print('===================')
        print(steering_out, throttle_out, tx.TOG, tx.BTNS)
        for button in Button:
            if tx.is_pressed(button):
                print(button.name)
        print('===================')
        

async def run_ble_client(input_queue: asyncio.Queue, output_queue: asyncio.Queue):

    print('starting BLE client')
    async def callback_handler(sender, data):
        global DATA
        DATA = data
        print(DATA)
        #await input_queue.put(data)
        

    async with BleakClient(addr) as client:
        await client.start_notify(UART_TX_CHAR_UUID, callback_handler)
        print('Connected')
        while True:
            msg = await output_queue.get()
            await client.write_gatt_char(UART_RX_CHAR_UUID, msg)

async def main(serial_port):
    print('running main')
    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()
    ble_task = run_ble_client(input_queue, output_queue)
    control_task =  run_control_task(input_queue, output_queue, serial_port)

    try:
        await asyncio.gather(ble_task, control_task)
    except KeyboardInterrupt:
        print('Stopping')
    serial_port.write('x'.encode())
    serial_port.flush()
    serial_port.close()
    print('Stopped')

if __name__ == "__main__":
    serial_port = serial.Serial(
        port="/dev/ttyTHS1",
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )
    time.sleep(1)
    serial_port.flush()
    serial_port.write(b"n,127,127")
    serial_port.write(b's')
    asyncio.run(main(serial_port))


