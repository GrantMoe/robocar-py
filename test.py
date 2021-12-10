#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import builtins
import logging
import asyncio
from enum import Enum
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

throttle_string = ['Auto', 'Manual']

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

menu = {
    'a': '',
    'b': '',
    'mode': '',
    'status': '',
    'main': '',
    'background': 'black'
}


def handle_disconnect(self):
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

def byte_to_pwm(in_byte):
    pwm = ( (in_byte - 0) / (256 - 0) ) * (2000 - 1000) + 1000
    return pwm

def is_pressed(btn):
    return BTNS & 1 << btn.value

def auto_menu(drive_mode, is_driving):
    m = {}
    m['mode'] = 'autonomous'
    m['main'] = throttle_string[auto_throttle]
    m['a'] = 'toggle throttle'
    if is_driving:
        m['status'] = 'driving'
        m['b'] = 'pause'
    else:
        m['status'] = 'paused'
        m['b'] = 'start'
    return m

def data_menu(recording, records=0):
    m = {}
    m['mode'] = 'data'
    m['main'] = f'Records: {records}'
    m['a'] = 'erase records'
    if recording:
        m['status'] = 'recording'
        m['b'] = 'pause recording'
    else:
        m['status'] = 'paused'
        m['b'] = 'start recording'
    return m

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


def erasing_menu(seconds):
    m = {}
    m['mode'] = 'data'
    m['status'] = 'erasing'
    m['main'] = f'Seconds: {seconds}' 
    m['b'] = 'confirm'
    m['a'] = 'cancel'
    return m

async def process_inputs():
    global menu, control_mode, drive_mode
    global auto_throttle
    global is_erasing, seconds_to_erase
    global is_recording, records
    # if the master start/stop switch is on
    if is_pressed(Button.CH_4):
        # handle things
        menu['background'] = 'black'
        # this could be more elegant
        if drive_mode == Drive_Mode.AUTO:
            if is_pressed(Button.TFT_A):
                if auto_throttle == Auto_Throttle.MANUAL:
                    auto_throttle = Auto_Throttle.AUTO
                else:
                    auto_throttle = Auto_Throttle.MANUAL
            menu = auto_menu()
            steering_pwm, throttle_pwm = auto_drive(auto_throttle)
        elif drive_mode == Drive_Mode.DATA:
            if is_erasing:
                is_recording = False
                if is_pressed(Button.TFT_B):
                    if is_recording:
                        is_recording = False
                    else: 
                        is_recording = True
                elif is_pressed(Button.TFT_A):
                    is_erasing = True
            else:
                if is_pressed(Button.TFT_B):
                    erase_records(seconds_to_erase)
                    is_erasing = False
                elif is_pressed(Button.TFT_A):
                    seconds_to_erase = 0
                    is_erasing = False
                elif is_pressed(Button.JOY_DOWN):
                    seconds_to_erase += 5
                elif is_pressed(Button.JOY_UP):
                    seconds_to_erase -= 5
                    seconds_to_erase = min(seconds_to_erase, 0)

            if is_erasing:
                menu = erasing_menu(seconds_to_erase)

                menu = data_menu(is_recording, records)
                

                steering_pwm, throttle_pwm = manual_drive()

        
    else:
        # STOP
        steering_pwm = STEERING_NEUTRAL
        throttle_pwm = THROTTLE_NEUTRAL
        menu['background'] = 'red'


    pass

# Test
async def send_output():
  global STR, THR, TOG, BTNS
  await asyncio.sleep(0.1)
  os.system('clear')
  print('===================')
  print(STR, THR, TOG, BTNS)
  for button in Button:
      if BTNS & 1 << button.value:
          print(button.name)
  print('===================')

    
async def run():
  
    print('Connecting')
    
    device = await BleakScanner.find_device_by_address(addr)
    
    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
   
        print(f'Connected to {device.name}')

        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
        
        while True:
            await process_inputs()
            await send_output()

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(run())
except KeyboardInterrupt:
    print('\nReceived Keyboard Interrupt')
finally:
    print('Program finished')
