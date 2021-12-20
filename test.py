#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio, evdev

tx = evdev.InputDevice('/dev/input/event5')

async def print_events(device):
    async for event in device.async_read_loop():
        print(device.path, evdev.categorize(event), sep=': ')

asyncio.ensure_future(print_events(tx))

loop = asyncio.get_event_loop()
loop.run_forever()