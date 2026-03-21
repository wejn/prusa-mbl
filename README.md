``` text
M105 ; ask temperature
M114 ; ask current pos
*M115 ; ask firmware info + store
```

``` text
$ python a.py /dev/ttyACM0 115200 customgcode.txt
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
