from evdev import InputDevice, ecodes


class XBoxController:

    def __init__(self, path):
        self.device = InputDevice(path)
        self.inputs = {
            'ABS_X': 0,
            'ABS_Z': 0,
            'ABS_RZ': 0,
        }

    def run(self):
        for event in self.device.read_loop():
            if event.type == ecodes.EV_ABS:
                if ecodes.ABS[event.code] in self.inputs:
                    self.inputs[event.code] = event.value

    def norm(self, val, v_min, v_max, low=0.0, high=1.0):
        return (high - low) * (val - v_min) / (v_max - v_min) + low

    def norm_axis(self, ax, low=0.0, high=1.0):
        ax_info = self.device.absinfo(ax)
        ax_val = self.inputs[ecodes.ABS[ax]]
        ax_min = ax_info.min
        ax_max = ax_info.max
        return (high - low) * (ax_val - ax_min) / (ax_max - ax_min) + low

    def get_steering(self, low=1000, high=2000):
        return self.norm_axis(ecodes.ABS_X, low, high)

    def get_throttle(self, low=1000, high=2000):
        t_pos = self.norm_axis(ecodes.ABS_RZ)
        t_neg = self.norm_axis(ecodes.ABS_Z)
        return self.norm(t_pos-t_neg, -1.0, 1.0, low, high)
