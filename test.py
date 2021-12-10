#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import builtins
import logging
import asyncio
from enum import Enum
from asyncio.tasks import ensure_future
from bleak import BleakClient
from bleak import BleakScanner

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

def is_pressed(btn):
    return BTNS & 1 << btn.value

def get_menu(menu_type):
    global menu
    data = ['m']
    m = bytearray()
    if menu_type == Menu_Mode.AUTO: 
        m.append('a')
        m.append(is_driving)
        m.append(auto_throttle)
    elif menu_type == Menu_Mode.DATA:
        m.append('d')
        m.append(is_recording)
        m.append(records)
    elif menu_type == Menu_Mode.ERASE:
        m.append('e')
        m.append(seconds_to_erase)
    else:
        m.append('m')
    mb = bytearray(m)
    length = len(mb)
    data.append(length)
    data.join(mb)
    menu = data

def manual_drive():
    return byte_to_pwm(STR), byte_to_pwm(THR)

def auto_drive(throttle):
    if throttle == Auto_Throttle.AUTO:
        # add prediction here
        return STEERING_NEUTRAL, THROTTLE_NEUTRAL
    if throttle == Auto_Throttle.MANUAL:
        return STEERING_NEUTRAL, byte_to_pwm(THR)

def erase_records(cutoff):
    # open CSV, open TEMP
    # copy records with time < cutoff
    # rename TEMP
    pass

def record_data():
    pass

async def control_worker():
    global menu, control_mode, drive_mode
    global auto_throttle
    global is_erasing, seconds_to_erase
    global is_recording, records
    global steering_pwm, throttle_pwm

    # drive mode
    if TOG > TRAIN_MIN:
        drive_mode = Drive_Mode.DATA
    elif TOG < AUTO_MAX:
        drive_mode = Drive_Mode.AUTO
    else:
        drive_mode = Drive_Mode.MANUAL

    # if the master start/stop switch is on
    if is_pressed(Button.CH_4):
        if drive_mode == Drive_Mode.AUTO:
            menu = get_menu(Menu_Mode.AUTO)
            # toggle auto throttle
            if is_pressed(Button.TFT_A):
                if auto_throttle == Auto_Throttle.MANUAL:
                    auto_throttle = Auto_Throttle.AUTO
                else:
                    auto_throttle = Auto_Throttle.MANUAL
            # get output based on throttle
            if is_driving:
                steering_pwm, throttle_pwm = auto_drive(auto_throttle)
            else:
                steering_pwm, throttle_pwm = manual_drive()
        elif drive_mode == Drive_Mode.DATA:
            if is_erasing:
                menu = get_menu(Menu_Mode.ERASE)
                # confirm erasure
                if is_pressed(Button.TFT_B):
                    erase_records(seconds_to_erase)
                    is_erasing = False
                # cancel erasure
                elif is_pressed(Button.TFT_A):
                    seconds_to_erase = 0
                    is_erasing = False
                # add seconds
                elif is_pressed(Button.JOY_UP):
                    seconds_to_erase += 5
                # remove seconds
                elif is_pressed(Button.JOY_DOWN):
                    seconds_to_erase -= 5
                    seconds_to_erase = min(seconds_to_erase, 0)
            else:
                menu = get_menu(Menu_Mode.DATA)
                record_data()
                # toggle recording
                if is_pressed(Button.TFT_B):
                    if is_recording:
                        is_recording = False
                    else: 
                        is_recording = True
                # start erasing
                elif is_pressed(Button.TFT_A):
                    is_recording = False
                    is_erasing = True
            steering_pwm, throttle_pwm = manual_drive()
        else:
            menu = get_menu(Menu_Mode.MANUAL)
            # just manual driving
            steering_pwm, throttle_pwm = manual_drive()
    else:
        # STOP
        steering_pwm = STEERING_NEUTRAL
        throttle_pwm = THROTTLE_NEUTRAL
    await asyncio.sleep(0.1)

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

    
async def run_ble():

    device = await BleakScanner.find_device_by_address(addr)

    def handle_disconnect(_: BleakClient):
        print('Device disconnected')
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_rx(_: int, data: bytearray):
        global STR, THR, TOG, BTNS
        data_list = data.split(b',')
        if len(data_list) >= 3:
            STR = data_list[0][0]
            THR = data_list[1][0]
            TOG = data_list[2][0]
            BTNS = data_list[3][0]
    
    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        while True:
            await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
            await asyncio.sleep(0.1)

async def run_control_loop():
    while True:
        await control_worker()
        await asyncio.sleep(0.1)

async def main():
    asyncio.gather(run_ble, run_control_loop)

if __name__ == "__main__":
    asyncio.run(main())


