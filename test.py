#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

# Default Adafruit BleUUART for now
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

# Test
async def send_output():
  global CH1, CH2, CH3, BTNS
  
  await asyncio.sleep(0.5)
  
  print(CH1, CH2, CH3, BTNS)
  for button in Button:
      if BTNS & 1 << button.value:
          print(button.name)
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
