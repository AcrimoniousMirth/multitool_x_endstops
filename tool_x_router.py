# Central router for dynamic X endstop management
#
# Copyright (C) 2026 Antigravity
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging

class ToolXRouter:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.tool_endstops = {}  # map from tool number to ToolXEndstop
        self.active_tool_number = -1
        self.mcu_router = EndstopRouter(self.printer)
        
        # Register x_virtual_endstop pin
        self.printer.lookup_object('pins').register_chip('tool_x_router', self)
        
        self.printer.register_event_handler("homing:home_rails_begin",
                                            self._handle_home_rails_begin)
        self.printer.register_event_handler('klippy:connect',
                                            self._handle_connect)

    def _handle_connect(self):
        self.tool_probe_endstop = self.printer.lookup_object('tool_probe_endstop', default=None)
        if self.tool_probe_endstop is None:
            logging.warning("tool_x_router: tool_probe_endstop NOT found. Detection will not work.")

    def add_tool_endstop(self, tool_x_endstop):
        if tool_x_endstop.tool in self.tool_endstops:
            raise Exception("Duplicate tool X endstop for tool %d" % (tool_x_endstop.tool,))
        self.tool_endstops[tool_x_endstop.tool] = tool_x_endstop
        self.mcu_router.add_mcu(tool_x_endstop.mcu_endstop)

    def setup_pin(self, pin_type, pin_params):
        if pin_type != 'endstop' or pin_params['pin'] != 'x_virtual_endstop':
            raise Exception("Tool X virtual endstop only useful as endstop pin")
        if pin_params['invert'] or pin_params['pullup']:
            raise Exception("Can not pullup/invert tool X virtual endstop")
        return self.mcu_router

    def _handle_home_rails_begin(self, homing_state, rails):
        # Check if X axis is being homed
        is_homing_x = False
        for rail in rails:
            for stepper in rail.get_steppers():
                if stepper.is_active_axis('x'):
                    is_homing_x = True
                    break
        
        if not is_homing_x:
            return

        logging.info("tool_x_router: X homing detected. Triggering tool detection.")
        
        if self.tool_probe_endstop is None:
            logging.error("tool_x_router: Cannot detect tool - tool_probe_endstop missing.")
            return

        # Trigger detection in tool_probe_endstop
        # Using the internal _detect_active_tool or the G-code command
        # Better to use the G-code command to ensure all logs and side effects happen
        gcode = self.printer.lookup_object('gcode')
        gcode.run_script_from_command("DETECT_ACTIVE_TOOL_PROBE")
        
        # Get the detected tool number
        status = self.tool_probe_endstop.get_status(self.printer.get_reactor().monotonic())
        detected_tool = status.get('active_tool_number', -1)
        
        self.set_active_tool(detected_tool)

    def set_active_tool(self, tool_number):
        if self.active_tool_number == tool_number:
            return
        
        logging.info("tool_x_router: Setting active tool for X endstop to T%d" % tool_number)
        
        tool_endstop = self.tool_endstops.get(tool_number)
        if tool_endstop:
            self.mcu_router.set_active_mcu(tool_endstop.mcu_endstop)
            self.active_tool_number = tool_number
        else:
            logging.warning("tool_x_router: No ToolXEndstop configured for T%d" % tool_number)
            self.mcu_router.set_active_mcu(None)
            self.active_tool_number = -1

# Routes commands to the selected tool endstop.
# Closely follows tool_probe_endstop.py's EndstopRouter
class EndstopRouter:
    def __init__(self, printer):
        self.printer = printer
        self.active_mcu = None
        self._mcus = []
        self._steppers = []
        self.set_active_mcu(None)

    def add_mcu(self, mcu_endstop):
        self._mcus.append(mcu_endstop)
        for s in self._steppers:
            mcu_endstop.add_stepper(s)

    def set_active_mcu(self, mcu_endstop):
        self.active_mcu = mcu_endstop
        # Update Wrappers
        if self.active_mcu:
            self.get_mcu = self.active_mcu.get_mcu
            self.home_start = self.active_mcu.home_start
            self.home_wait = self.active_mcu.home_wait
            self.query_endstop = self.active_mcu.query_endstop
        else:
            self.get_mcu = self.get_default_mcu
            self.home_start = self.on_error
            self.home_wait = self.on_error
            self.query_endstop = self.on_error

    def get_default_mcu(self):
        return self.printer.lookup_object('mcu')

    def add_stepper(self, stepper):
        self._steppers.append(stepper)
        for m in self._mcus:
            m.add_stepper(stepper)
            
    def get_steppers(self):
        return list(self._steppers)

    def on_error(self, *args, **kwargs):
        raise self.printer.command_error("Cannot interact with X endstop - no active tool detected.")

def load_config(config):
    return ToolXRouter(config)
