#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio, evdev

# mouse = evdev.InputDevice('/dev/input/event4')
dev = evdev.InputDevice('/dev/input/event17')

async def print_events(device):
    async for event in device.async_read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            print(device.path, evdev.categorize(event), sep=': ')

# for device in mouse, keybd:
asyncio.ensure_future(print_events(dev))

loop = asyncio.get_event_loop()
loop.run_forever()