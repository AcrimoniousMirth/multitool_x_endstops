# Klipper Toolchanger Dynamic X Endstop Addon

This addon extends the [klipper-toolchanger](https://github.com/viesturz/klipper-toolchanger) to support dynamic X endstop switching based on the active tool detected during homing.

## Features
- Automatic tool detection at the start of X homing.
- Dynamic switching of the X endstop pin based on the detected tool.

## Installation
### Automatic installation

The module can be installed into an existing Klipper installation with an install script. 

    cd ~
    git clone https://github.com/AcrimoniousMirth/multitool_x_endstops.git
    cd multitool_x_endstops
    ./install-multitool_x_endstops.sh

If your directory structure differs from the usual setup you can configure the
installation script with parameters:

    ./install-multitool_x_endstops.sh [-k <klipper path>] [-s <klipper service name>] [-c <configuration path>]

### Manual installation
1. Clone the repository:
    `cd ~`
    `git clone https://github.com/AcrimoniousMirth/multitool_x_endstops.git`
2. Stop Klipper: `sudo systemctl stop klipper`
3. Link the file (adjust paths as needed):
   `ln -sf ~/multitool_x_endstops/src/multitool_x_endstop.py ~/klipper/klippy/extras/multitool_x_endstop.py`
   `ln -sf ~/multitool_x_endstops/src/multitool_x_router.py ~/klipper/klippy/extras/multitool_x_router.py`
4. Start Klipper: `sudo systemctl start klipper`

## Configuration

### 1. Tool X Router
Add the following to your main `printer.cfg` to register the virtual pin:

```ini
[tool_x_router]
```

### 2. Stepper X Endstop
Update your `[stepper_x]` section to use the virtual endstop pin provided by the router:

```ini
[stepper_x]
# ... other config ...
endstop_pin: tool_x_router:x_virtual_endstop
```

### 3. Tool Endstops
Define the specific pins for each toolhead in your toolhead configuration files (e.g., `toolhead_0.cfg`, `toolhead_1.cfg`):

```ini
# For Tool 0
[tool_x_endstop T0]
pin: example:PB0  # Replace with the actual pin on T0
tool: 0

# For Tool 1
[tool_x_endstop T1]
pin: example:PB1  # Replace with the actual pin on T1
tool: 1
```

## How it works
When an X homing move is requested (e.g., via `G28 X`), the `tool_x_router` intercepts the `homing:home_rails_begin` event. It then runs `DETECT_ACTIVE_TOOL_PROBE` (from `tool_probe_endstop.py`) to determine which tool is currently attached. Once a tool is identified, the router switches the active endstop pin for the X axis to the pin defined in the corresponding `[tool_x_endstop]` section.
