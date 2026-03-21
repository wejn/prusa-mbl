# Průša Mesh Bed Level visualizer

This is a bunch of scripts that allow you to visualize
the bed level of your Průša 3D printer.

Only tested on Core One +.

## Credits

This would be significantly harder if it weren't for a few existing "wheels".

So, credits where credits are due:

- [OctoPrint bed visualizer
  gcode](https://forum.prusa3d.com/forum/prusa-core-one-hardware-firmware-and-software-help/octoprint-bed-visualizer-gcode/)
  thread, and namely [Biomech's
  post](https://forum.prusa3d.com/forum/postid/750846/)

- Claude.ai


## Dumping bed mesh data

In order to dump bed mesh data, I've created the `run_gcode.py` utility.

Requires python's serial package (`python3-serial` on Debian, `py3-pyserial`
on alpine, `pyserial` via pip).

To use it, you simply run it against your printer, from a Linux distro.

E.g.:

``` sh
$ python run_gcode.py /dev/ttyACM0 115200
```

It executes the default gcode (see the source for details) and dumps
out a text files with the mesh in two formats:
- `gcode_G29_T0_{TIMESTAMP}.txt` as the default (use for the visualizer)
- `gcode_G29_T1_{TIMESTAMP}.txt` as CSV-friendly

The default code was fished out of default bootstrap gcode that PrusaSlicer
2.9.4 generated for my Core One +.


### Running custom gcode

Should you want to run your own gcode, put it in a file, and supply that
as additional parameter.

Any gcode that you prefix with a star (`*`) will be captured to a file.

For example, say I have `customgcode.txt` file with:

``` text
M105 ; ask temperature
M114 ; ask current pos
*M115 ; ask firmware info + store
```

I can run it thusly:

``` text
$ python run_gcode.py /dev/ttyACM0 115200 customgcode.txt
** Verifying printer presence with M115 …
>> M115
<< FIRMWARE_NAME:Prusa-Firmware-Buddy 6.4.0+11974 (Github) SOURCE_CODE_URL:https://github.com/prusa3d/Prusa-Firmware-Buddy PROTOCOL_VERSION:1.0 MACHINE_TYPE:Prusa-COREONE EXTRUDER_COUNT:1 UUID:239ba2dd-2509-11f1-b239-0010182e9fa6
<< Cap:SERIAL_XON_XOFF:0
<< Cap:BINARY_FILE_TRANSFER:0
<< Cap:EEPROM:0
<< Cap:VOLUMETRIC:1
<< Cap:AUTOREPORT_TEMP:1
<< Cap:PROGRESS:0
<< Cap:PRINT_JOB:1
<< Cap:AUTOLEVEL:1
<< Cap:Z_PROBE:1
<< Cap:LEVELING_DATA:1
<< Cap:BUILD_PERCENT:0
<< Cap:SOFTWARE_POWER:1
<< Cap:TOGGLE_LIGHTS:0
<< Cap:CASE_LIGHT_BRIGHTNESS:0
<< Cap:EMERGENCY_PARSER:0
<< Cap:PROMPT_SUPPORT:0
<< Cap:AUTOREPORT_SD_STATUS:0
<< Cap:THERMAL_PROTECTION:1
<< Cap:MOTION_MODES:0
<< Cap:CHAMBER_TEMPERATURE:1
<< ok
** Printer detected.
 
>> M105 ; ask temperature
<< ok T:40.00/39.00 B:29.64/10.00 X:32.00/36.00 A:40.45/0.00 @:0 B@:0 C@:27.65 HBR@:0
>> M114 ; ask current pos
<< X:0.00 Y:-4.00 Z:15.00 E:-2.00 Count A:-399 B:397 Z:6000
<< ok
>> M115 ; ask firmware info + store
<< FIRMWARE_NAME:Prusa-Firmware-Buddy 6.4.0+11974 (Github) SOURCE_CODE_URL:https://github.com/prusa3d/Prusa-Firmware-Buddy PROTOCOL_VERSION:1.0 MACHINE_TYPE:Prusa-COREONE EXTRUDER_COUNT:1 UUID:239ba2dd-2509-11f1-b239-0010182e9fa6
<< Cap:SERIAL_XON_XOFF:0
<< Cap:BINARY_FILE_TRANSFER:0
<< Cap:EEPROM:0
<< Cap:VOLUMETRIC:1
<< Cap:AUTOREPORT_TEMP:1
<< Cap:PROGRESS:0
<< Cap:PRINT_JOB:1
<< Cap:AUTOLEVEL:1
<< Cap:Z_PROBE:1
<< Cap:LEVELING_DATA:1
<< Cap:BUILD_PERCENT:0
<< Cap:SOFTWARE_POWER:1
<< Cap:TOGGLE_LIGHTS:0
<< Cap:CASE_LIGHT_BRIGHTNESS:0
<< Cap:EMERGENCY_PARSER:0
<< Cap:PROMPT_SUPPORT:0
<< Cap:AUTOREPORT_SD_STATUS:0
<< Cap:THERMAL_PROTECTION:1
<< Cap:MOTION_MODES:0
<< Cap:CHAMBER_TEMPERATURE:1
<< ok
 
** M115 ; ask firmware info + store saved to: gcode_M115_20260321_103328.txt
 
** Done.
```

## Visualizing the bed mesh

You have two options.

### Using matplotlib

``` sh
$ python bedviz.py gcode_G29_T0_20260321_100707.txt
```

will get you interactive UI with matplotlib:

![matplotlib ui](https://raw.githubusercontent.com/wejn/prusa-mbl/master/screenshots/matplotlib.png)

### Using plotly in a browser

Opening `bedviz.html` in your browser and plopping in your data into the text field
will give you HTML visualizer using plotly javascript library:

![plotly ui](https://raw.githubusercontent.com/wejn/prusa-mbl/master/screenshots/plotly.png)
