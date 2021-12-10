#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import builtins
import logging
import asyncio
import serial
import time
from enum import Enum
from asyncio.tasks import ensure_future
from bleak import BleakClient
from bleak import BleakScanner
from serial.serialposix import Serial

# Adafruit nrf58320
addr = "EF:EB:FD:C7:F8:DA"

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

class Control_Mode(Enum):
    DRIVE = 0
    MENU = 1

class Drive_Mode(Enum):
    AUTO = 0
    DATA = 1
    MANUAL = 2

class Auto_Throttle(Enum):
    AUTO = 0
    MANUAL = 1

class Menu_Mode(Enum):
    AUTO = 0
    DATA = 1
    ERASE = 2
    MANUAL = 3

TRAIN_MIN = 170
AUTO_MAX = 85

menu = []


is_driving = False
is_recording = False
is_erasing = False


seconds_to_erase = 0

# Default Adafruit BleUUART for now
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

STR = 0
THR = 0
TOG = 0
BTNS = 0
control_mode = 0
drive_mode = 0
auto_throttle = 0

records = 0

PWM_MIN = 1000
PWM_MAX = 2000
STEERING_NEUTRAL = 1500
THROTTLE_NEUTRAL = 1500

steering_pwm = STEERING_NEUTRAL
throttle_pwm = THROTTLE_NEUTRAL


async def update_controller(client):
    global menu
    await client.write_gatt_char(UART_RX_CHAR_UUID, menu)

def byte_to_pwm(in_byte):
    pwm = ( (in_byte - 0) / (256 - 0) ) * (2000 - 1000) + 1000
    return pwm

def is_pressed(buttons, btn):
    return buttons & 1 << btn.value


def get_menu(menu_type):
    menu_fields = ''
    if menu_type == Menu_Mode.AUTO: 
        menu_fields = f'a,{int(is_driving)},{int(auto_throttle)}'
    elif menu_type == Menu_Mode.DATA:
        menu_fields = f'd,{int(is_recording)},{records}'
    elif menu_type == Menu_Mode.ERASE:
        menu_fields = f'e,{seconds_to_erase}'
    else:
        menu_fields = 'm'
    return bytearray(menu_fields, 'utf-8')
    
def manual_drive(str, thr):
    # return byte_to_pwm(str), byte_to_pwm(thr)
    # simplify it for now
    return str, thr

def auto_drive(thr, throttle_mode):
    if throttle_mode == Auto_Throttle.AUTO:
        # TODO
        # return STEERING_NEUTRAL, THROTTLE_NEUTRAL
        return 127, 127
    if throttle_mode == Auto_Throttle.MANUAL:
        # return STEERING_NEUTRAL, byte_to_pwm(thr)
        return 127, thr


def erase_records(cutoff):
    # open CSV, open TEMP
    # copy records with time < cutoff
    # rename TEMP
    pass

def record_data():
    pass


# Test
async def send_output():
  global STR, THR, TOG, BTNS
  os.system('clear')
  print('===================')
  print(STR, THR, TOG, BTNS)
  for button in Button:
      if BTNS & 1 << button.value:
          print(button.name)
  print('===================')
  await asyncio.sleep(0.1)


async def run_control_task(queue: asyncio.Queue, serial_port: serial.Serial):
    while True:
        data = await queue.get()
        data_list = data.split(b',')
        if len(data_list) >= 3:
            STR = data_list[0][0]
            THR = data_list[1][0]
            TOG = data_list[2][0]
            BTNS = data_list[3][0]

        # drive mode
        if TOG > TRAIN_MIN:
            drive_mode = Drive_Mode.DATA
        elif TOG < AUTO_MAX:
            drive_mode = Drive_Mode.AUTO
        else:
            drive_mode = Drive_Mode.MANUAL

        # if the master start/stop switch is on
        if is_pressed(BTNS, Button.CH_4):
            if drive_mode == Drive_Mode.AUTO:
                menu = get_menu(Menu_Mode.AUTO)
                # toggle auto throttle
                if is_pressed(BTNS, Button.TFT_A):
                    if auto_throttle == Auto_Throttle.MANUAL:
                        auto_throttle = Auto_Throttle.AUTO
                    else:
                        auto_throttle = Auto_Throttle.MANUAL
                # get output based on throttle
                if is_driving:
                    steering_pwm, throttle_pwm = auto_drive(auto_throttle)
                else:
                    steering_pwm, throttle_pwm = manual_drive(STR, THR)
            elif drive_mode == Drive_Mode.DATA:
                if is_erasing:
                    menu = get_menu(Menu_Mode.ERASE)
                    # confirm erasure
                    if is_pressed(BTNS, Button.TFT_B):
                        erase_records(seconds_to_erase)
                        is_erasing = False
                    # cancel erasure
                    elif is_pressed(BTNS, Button.TFT_A):
                        seconds_to_erase = 0
                        is_erasing = False
                    # add seconds
                    elif is_pressed(BTNS, Button.JOY_UP):
                        seconds_to_erase += 5
                    # remove seconds
                    elif is_pressed(BTNS, Button.JOY_DOWN):
                        seconds_to_erase -= 5
                        seconds_to_erase = min(seconds_to_erase, 0)
                else:
                    menu = get_menu(Menu_Mode.DATA)
                    record_data()
                    # toggle recording
                    if is_pressed(BTNS, Button.TFT_B):
                        if is_recording:
                            is_recording = False
                        else: 
                            is_recording = True
                    # start erasing
                    elif is_pressed(BTNS, Button.TFT_A):
                        is_recording = False
                        is_erasing = True
                steering_pwm, throttle_pwm = manual_drive(STR, THR)
            else:
                menu = get_menu(Menu_Mode.MANUAL)
                # just manual driving
                steering_pwm, throttle_pwm = manual_drive(STR, THR)
        else:
            # STOP
            steering_pwm = STEERING_NEUTRAL
            throttle_pwm = THROTTLE_NEUTRAL
        os.system('clear')
        print('===================')
        print(steering_pwm, throttle_pwm, TOG, BTNS)
        for button in Button:
            if BTNS & 1 << button.value:
                print(button.name)
        print('===================')
        serial_port.flush()
        output_string = f"n,{steering_pwm},{throttle_pwm}"  # it's bytes not pwm
        serial_port.write(output_string.encode())
        

async def run_ble_client(queue: asyncio.Queue):
    async def callback_handler(sender, data):
        await queue.put(data)
    async with BleakClient(addr) as client:
        await client.start_notify(UART_TX_CHAR_UUID, callback_handler)
        await asyncio.sleep(9999999) # shrug


async def main(serial_port):
    queue = asyncio.Queue()
    ble_task = run_ble_client(queue)
    control_task =  run_control_task(queue, serial_port)
    await asyncio.gather(ble_task, control_task)


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
    asyncio.run(main())


