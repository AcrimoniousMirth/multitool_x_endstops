# Tool-specific X endstop configuration
#
# Copyright (C) 2026 Antigravity
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging

class ToolXEndstop:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.tool = config.getint('tool')
        self.name = config.get_name()
        
        # We need to wrap the pin into an MCU endstop object.
        # We use a custom wrapper to ensure it attaches to X steppers.
        self.mcu_endstop = ProbeEndstopWrapper(config, 'x')
            
        # Register with the router
        self.router = self.printer.load_object(config, "tool_x_router")
        self.router.add_tool_endstop(self)

# Endstop wrapper that enables axis-specific stepper attachment
# Adapted from klipper-toolchanger's tools_calibrate.py
class ProbeEndstopWrapper:
    def __init__(self, config, axis):
        self.printer = config.get_printer()
        self.axis = axis
        # Create an "endstop" object to handle the probe pin
        ppins = self.printer.lookup_object('pins')
        pin = config.get('pin')
        ppins.allow_multi_use_pin(pin.replace('^', '').replace('!', ''))
        pin_params = ppins.lookup_pin(pin, can_invert=True, can_pullup=True)
        mcu = pin_params['chip']
        self.mcu_endstop = mcu.setup_pin('endstop', pin_params)
        # Wrappers
        self.get_mcu = self.mcu_endstop.get_mcu
        self.add_stepper = self.mcu_endstop.add_stepper
        self.get_steppers = self.mcu_endstop.get_steppers
        self.home_start = self.mcu_endstop.home_start
        self.home_wait = self.mcu_endstop.home_wait
        self.query_endstop = self.mcu_endstop.query_endstop

    def get_position_endstop(self):
        return 0.

def load_config_prefix(config):
    return ToolXEndstop(config)
