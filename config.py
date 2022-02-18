
# LAPTOP
# default_controller_path = '/dev/input/event17'

# NANO
default_controller_path = '/dev/input/event5'

# THIS IS FOR NANO
default_serial_port = "/dev/ttyTHS1"

controller_types = [
    'xbox',
    'ble_gamepad'
]
default_controller_type = 'ble_gamepad'


# Menus
# format 'm', size, [a, d, e, m], bool(s), value(s)
AUTO_MENU = {
    'a': 'toggle_throttle',
    'b': ['start', 'pause'], # is_driving
    'main': ['manual', 'auto'],  # auto_throttle
    'mode': 'autonomous',
    'status': ['paused', 'driving'], # is_driving
}

DATA_MENU = {
    'a': 'erase_records',
    'b': ['start', 'pause'],  # is_recording
    'main': 'number of records', # records
    'mode': 'data',
    'status': ['paused', 'recording'], # is_recording    
}

ERASE_MENU = {  # is_erasing
    'a': 'confirm',
    'b': 'cancel',
    'main': 'seconds to erase', # seconds
    'mode': 'data',
    'status': ['erasing'],    
}

MANUAL_MENU = {
    'a': '',
    'b': '',
    'main': '',
    'mode': 'manual',
    'status': '',    
}
