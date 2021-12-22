""" A module to hold my custom HID controller class. """
from evdev import InputDevice, ecodes

class BleGamePad:

    STEERING_AXIS = ecodes.ABS_X
    THROTTLE_AXIS = ecodes.ABS_Y
    MODE_AXIS = ecodes.ABS_RY
    STATUS_AXIS = ecodes.ABS_RZ
    # TODO: ecodes for butan when recording starts

    def __init__(self, path):
        self.device = InputDevice(path);
        self.inputs = {
            self.STEERING_AXIS: 0,
            self.THROTTLE_AXIS: 0,
            self.MODE_AXIS: 0,
            self.STATUS_AXIS: 0,
        }
        # self.driving = False

    def run(self):
        """ Query and process relevant evdev events. """
        for event in self.device.read_loop():
            # if not self.esc_started:
            #     if event.code == ecodes.BTN_START:
            #         self.esc_started = True
            if event.type == ecodes.EV_KEY:
                print(event.code) # testing dpad/hat
            if event.type == ecodes.EV_ABS:
                if event.code in self.inputs:
                    self.inputs[event.code] = self.process_axis(event.code, event.value)

    def is_started(self):
        """ Check if tx is in drive mode"""
        return self.inputs['STATUS_AXIS'] < 0

    def norm(self, val, v_min, v_max, low=0.0, high=1.0):
        """ Norm a number. """
        return (high - low) * (val - v_min) / (v_max - v_min) + low

    def norm_axis(self, axis, low=0.0, high=1.0):
        """ Norm an axis. """
        ax_val = self.inputs[axis]
        ax_info = self.device.absinfo(axis)
        ax_min = ax_info.min
        ax_max = ax_info.max
        return self.norm(ax_val, ax_min, ax_max, low, high)

    def get_steering(self, low=-1.0, high=1.0):
        """ Return normed steering input. """
        return self.norm_axis(ecodes.ABS_X, low, high)

    def get_throttle(self, low=-1.0, high=1.0):
        """ Return normed combined throttle input. """
        return self.norm(self.THROTTLE_AXIS, -1.0, 1.0, low, high)

    # TODO: verify axis info
    def process_axis(self, axis, val):
        """ Constrain/process abs event. """
        ax_info = self.device.absinfo(axis)
        if val > ax_info.max:
            val = ax_info.max
        elif val < ax_info.min:
            val = ax_info.min
        if abs(val) < ax_info.flat:
            return 0
        if abs(self.inputs[axis] - val) < ax_info.fuzz:
            return self.inputs[axis]
        # else
        return val