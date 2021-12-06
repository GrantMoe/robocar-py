# RoboCar-Py
A variation on a common theme. Python scripts to run on a Jetson Nano mounted on my 1/10 scale DIY Robocar.

## Hardware
### Car
* Jetson Nano
* Teesny 4.0

The Teensy is serving as a glorified PWM driver. It receives steering and throttle inputs from the Nano via a serial connection (UART), then sends the correct pulse width signals to the steering servo and throttle. 

It will be given more to do in the future, probably.

### Transmitter

[robocar-tx](https://github.com/GrantMoe/robocar-tx): BLE Feather [Adafruit Feather nRF52 Bluefruit LE](https://www.adafruit.com/product/3406) grafted to the remains of an RC transmitter housing.

## Software

User input is provided by a Bluetooth XBox controller paired to the Jetson Nano. I don't like driving with the thumbsticks, and XBox controllers can be a bit iffy with Jetson Nanos for whatever reason, so I am in the process of switching to a more direct GATT-based approach. An Arduino sketch running on the Feather in the transmitter unit polls various knobs and switches and potentiometers then sends the info over to the Nano.

Everything is hard/hand coded for now.

In theory PWM output could be handled by the Nano itself. I might explore that later.
