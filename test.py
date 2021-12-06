#/usr/bin/python3




# -*- coding: utf-8 -*-
"""
/******************************************************************* 
  ProtoStax Arduino Nano 33 BLE Sense RGB LED Control Central Device
  This is a example sketch for controlling the RGB LED on an 
  Arduino Nano 33 BLE Sense with Bluetooth over Python  
   
  Items used:
  Arduino Nano 33 BLE Sense
  ProtoStax for BreadBoard/Custom Boards - 
      - to house and protect the Nano and allow for other circuitry 
      --> https://www.protostax.com/collections/all/products/protostax-for-breadboard
  
  The Nano publishes a Bluetooth LE Client profile with Characteristics for the Red, Green, 
  and Blue components of the onboard RGB LED. These can be read and written to
  control the LED colors.
  This program toggles the R,G,B LEDs based on user input. Run the python program from your computer
  (PC, Mac or Linux) that has Bluetooth support and the requisite python packages - 
  you can then read and set the on/off states of the 3 colors. 
  
  The Red, Green and Blue colors of the onboard RGB LED can only be turned on or off. 
  It is not possible to use PWM to mix colors, unfortunately, based on how the Arduino 
  Nano BLE Sense board is configured.
  
  We write a value of 1 to turn on a color and 0 to turn it off. The user inputs 
  a string that can contain r,g,b (or any combination) and those colors will be toggled. 
  The Arduino Nano 33 BLE Sense is chockful of other sensors - you can similarly expose 
  those sensors data as Characteristics
 
  Written by Sridhar Rajagopal for ProtoStax
  BSD license. All text above must be included in any redistribution
 */
"""

import logging
import asyncio
from enum import Enum
from bleak import BleakClient
from bleak import BleakScanner

# Adafruit nrf58320
addr = "EF:EB:FD:C7:F8:DA"

# bit mask
class Button(Enum):
    JOY_UP  = 0
    JOY_DOWN = 1
    JOY_LEFT = 2
    JOY_RIGHT = 3
    JOY_SELECT = 4
    TFT_A = 5
    TFT_B = 6
    CH_4 = 7

# Default Adafruit BleUUART (for now?) 
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

CH1 = 0
CH2 = 0
CH3 = 0
BTNS = 0


def handle_disconnect():
    print('Device disconnected')
    for task in asyncio.all_tasks():
        task.cancel()


def handle_rx(_: int, data: bytearray):
    global CH1, CH2, CH3, BTNS
    data_list = data.split(b',')
    btns = data_list[3][0]
    CH1 = data_list[0][0]
    CH2 = data_list[1][0]
    CH3 = data_list[2][0]
    BTNS = data_list[3][0]
    # print(f'(ch1: {data_list[0][0]}, ch2: {data_list[1][0]}, ch3: {data_list[2][0]}, btns: {data_list[3][0]}')

# Seems to work
async def send_output():
    global CH1, CH2, CH3, BTNS
    await asyncio.sleep(0.5)
    print(CH1, CH2, CH3, BTNS)
    for btn in BTNS:
        if BTNS & 1 << btn.value:
            print(btn.name)
    print('----')

async def run():

    print('Connecting')

    device = await BleakScanner.find_device_by_address(addr)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        print(f'Connected to {device.name}')

        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
           
        while True:
            # await loop.run_in_executor(None, )
            await send_output()

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(run())
except KeyboardInterrupt:
    print('\nReceived Keyboard Interrupt')
finally:
    print('Program finished')