# Průša Mesh Bed Level tools

This is a bunch of scripts that allow you to visualize
and correct the bed level of your Průša 3D printer.

Only tested on Core One+.

There are two tools:

1. [Visualizer](#visualizer): allows you to visualize your bed using MBL
1. [Bed leveler](#bed-leveler): allows you to correct uneven Core One+ bed

To use either, you _need_ access to your printer's serial port. Either
from a PC (laptop), or using a dedicated raspberry pi / esp32 dongle.

## Visualizer

In short, this allows you to visualize the bed mesh using built-in MBL
system (`G29` gcode, the "unified bed leveling") from Marlin firmware.

### Dumping bed mesh data

In order to dump bed mesh data, I've created the `run_gcode.py` utility.

Requires python's serial package (`python3-serial` on Debian, `py3-pyserial`
on alpine, `pyserial` via pip).

To use it, you simply run it against your printer, from a Linux distro,
with a payload you want to execute.

E.g.:

``` sh
$ python run_gcode.py /dev/ttyACM0 115200 mbl-60c.gcode
```

The `mbl-60c.gcode` executes the default gcode (see the file for details)
and dumps out three text files with the mesh, in two formats:
- `gcode_G29_T_{TIMESTAMP}.txt` the sparse mesh (actual points measured)
- `gcode_G29_T0_{TIMESTAMP}.txt` as the default (use for the visualizer)
- `gcode_G29_T1_{TIMESTAMP}.txt` as CSV-friendly

The default code was fished out of default bootstrap gcode that PrusaSlicer
2.9.4 generated for my Core One +. It uses 60°C bed.

There are other variants for other bed temps: `mbl-40c.gcode`, `mbl-80c.gcode`.

If you want mesh without any heat up (completely cold), run `mbl-cold.gcode`
instead.

If you want the measurements at standoff locations, run `probe-standoffs.gcode`.


#### Running custom gcode

Should you want to run your own gcode, put it in a file, and supply that
as additional parameter.

Any gcode that you prefix with a star (`*`) will be captured to a file.

For example, say I have `custom.gcode` file with:

``` text
M105  ; ask temperature
M114  ; ask current pos
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

>> M105  ; ask temperature
<< ok T:40.00/39.00 B:29.64/10.00 X:32.00/36.00 A:40.45/0.00 @:0 B@:0 C@:27.65 HBR@:0
>> M114  ; ask current pos
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

### Visualizing the bed mesh

You have two options.

#### Using matplotlib

``` sh
$ python bedviz.py gcode_G29_T0_20260321_100707.txt
```

will get you interactive UI with matplotlib:

![matplotlib ui](https://raw.githubusercontent.com/wejn/prusa-mbl/master/screenshots/matplotlib.png)

#### Using plotly in a browser

Opening `bedviz.html` in your browser and plopping in your data into the text field
will give you HTML visualizer using plotly javascript library:

![plotly ui](https://raw.githubusercontent.com/wejn/prusa-mbl/master/screenshots/plotly.png)

## Bed leveler

This tool allows you to correct bed level using a rather involved procedure.

Details in [my blog post](http://wejn.org/2026/03/leveling-prusa-core-one-bed/).

This uses undocumented [`G29 P10` gcode](https://github.com/prusa3d/Prusa-Firmware-Buddy/blob/b91eeda0c16a9931126ea065f2fa2bcc8a983b8d/lib/Marlin/Marlin/src/feature/bedlevel/ubl/ubl_G29.cpp#L601)
I discovered in Průša's Firmware Buddy source.

The idea to get a level bed is:

1. Run Core One built in "Z Alignment Calibration" (from "Control" → "Calibrations & Tests" menu)
1. Probe the 9 points (standoffs) on which the bed rests.
1. From the 9 points choose 3 that define plane, calculate offset to make them level.
1. Project the offset plane to suspension points (the left/right/back threaded rods),
   calculate needed offsets.
1. For the rest of the points, calculate needed shim distance.

Obviously all of the adjustments must be positive, as we can't really twist
the bed lower, eh? But I allow for -0.025mm "air gap".

Sounds good? Let's do it.

### Calculating the bed correction

So you run:

``` sh
$ python run_gcode.py /dev/ttyACM0 115200 probe-standoffs.gcode
```

which probes the points of the 9 standoffs and writes them out into
`G29_P10_V4_*.txt` files.

Then you run either `parse-bedmesh.py` or `parse-bedmesh.rb` from the same
directory, which gets you the mesh offsets:

``` ruby
# ruby parse-bedmesh.rb
MESH_Z = [
  # x=15    x=125   x=230   (for each y row)
   0.203,   0.311,   0.602,  # y=220
   0.102,   0.147,   0.464,  # y=115
  -0.338,  -0.378,   0.009,  # y=10
].freeze
```

Depending on your pain tolerance, you either plug this output into
the `bed-leveling-calculator.rb` and run it, or you open the
`bed-leveling-calculator.html` in your browser, and plug in the numbers
manually.

Here's how it looks for the mesh above:

``` sh
$ ruby bed-leveling-calculator.rb
========================================================================
  PLANE LEVELING — ALL VALID SOLUTIONS (ranked by total lift, ascending)
========================================================================

------------------------------------------------------------------------
  Rank 1  |  Reference points: MP(x=15,y=220), MP(x=230,y=220), MP(x=15,y=115)
  Total lift score: 2.2057

  Suspension point Z adjustments:
    S1 (-28.1, -37.2)  =>  +  0.5920
    S2 (290.91, -37.2)  =>  +  0.0000
    S3 (125.0, 274.3)  =>  +  0.0083

  Shim distances at mesh points (+ = shim needed, - = air gap):
       x=15      x=125     x=230
    y=220      0.0000    0.0961    0.0000
    y=115      0.0000    0.1591    0.0370
    y=10       0.3390    0.5831    0.3910

------------------------------------------------------------------------
  Rank 2  |  Reference points: MP(x=230,y=220), MP(x=15,y=115), MP(x=230,y=115)
  Total lift score: 2.2349

  Suspension point Z adjustments:
    S1 (-28.1, -37.2)  =>  +  0.6672
    S2 (290.91, -37.2)  =>  +  0.1301
    S3 (125.0, 274.3)  =>  +  0.0000

  Shim distances at mesh points (+ = shim needed, - = air gap):
       x=15      x=125     x=230
    y=220      0.0370    0.1142   -0.0000
    y=115     -0.0000    0.1402    0.0000
    y=10       0.3020    0.5272    0.3170

------------------------------------------------------------------------
  Rank 3  |  Reference points: MP(x=15,y=115), MP(x=15,y=10), MP(x=230,y=10)

[...]

========================================================================
  Total valid solutions: 6  (out of 84 combinations tried)
========================================================================
```

whereas from the HTML you'd get:

![bed leveling calculator ui](https://raw.githubusercontent.com/wejn/prusa-mbl/master/screenshots/blc.png)

### Correcting the bed

The hardware part is mostly up to you.

I used appropriately thick "Feeler's gauge" under the threaded rods with
the "Z Alignment Calibration" to correct the suspension points. This persists
as long as you don't run the Z align calibration again. For permanent solution
you can later on print up an appropriate [Prusa CORE ONE BedLevel Correction
& Dust Cover](https://www.printables.com/model/1289015).

For the shims under the standoffs, you have to take the bed off, unscrew each
of the standoffs, put an appropriately thick (thin) shim between the bed
carriage and the standoff, and tighten it appropriately.

Btw, the standoff cubes are 8x10 (8mm high) with 2.5mm holes in them.

As shimming material, you can either (ab)use a can of coke (0.15mm thick)
to make your own shims, or buy some "ultra thin washer" from AliEx (or similar)
if you want more pro solution.

Afterwards, you can verify with either the `probe-standoffs.gcode`,
or with the full blown [mesh visualizer](#visualizer) cycle.

### My result

My resulting bed then ended up thusly:

``` ruby
MESH_Z = [
  # x=15    x=125   x=230   (for each y row)
  -0.062,  -0.008,   0.049,  # y=220
  -0.022,  -0.021,   0.024,  # y=115
   0.038,  -0.023,   0.018,  # y=10
].freeze
```

and full bed mesh:

![bed after adjustment](https://raw.githubusercontent.com/wejn/prusa-mbl/master/screenshots/bed-after.png)

... and it's this ~bad mostly because I don't have _exact_ shims on hand
(think: thin 0.1mm washers) and had to improvize by cutting up a can of coke.

Still, night and day, compared to the original (above).

## Credits

Developing this would be significantly harder if it weren't for a few existing "wheels".

So, credits where credits are due:

- [OctoPrint bed visualizer
  gcode](https://forum.prusa3d.com/forum/prusa-core-one-hardware-firmware-and-software-help/octoprint-bed-visualizer-gcode/)
  thread, and namely [Biomech's post](https://forum.prusa3d.com/forum/postid/750846/)

- Claude.ai

- [G29 - Bed Leveling (Unified)](https://marlinfw.org/docs/gcode/G029-ubl.html)
  Marlin documentation

- [Prusa-Firmware-Buddy](https://github.com/prusa3d/Prusa-Firmware-Buddy/)

- [Prusa CORE One - Full CAD Assembly](https://www.printables.com/model/1520471-prusa-core-one-full-cad-assembly)
