M117 Prelude
M105          ; ask current temp
M114          ; ask current position

M117 Bed leveling prep
G90           ; use absolute coordinates
G28           ; home all without mesh bed level
M84 E         ; turn off E motor

M117 MBL procedure
M84 E                     ; turn off E motor
G29 P1                    ; invalidate mbl & probe print area
*G29 T                    ; capture bed topography (sparse)
G29 P1 X150 Y0 W100 H20 C ; probe near purge place
G29 P3.2                  ; interpolate mbl probes
G29 P3.13                 ; extrapolate mbl outside probe area

M117 Record
*G29 T0       ; capture bed topography (full)
*G29 T1       ; capture bed topography (full, csv)

M117 Cleanup
M104 S0             ; turn off temperature
M140 S0             ; turn off heatbed
M107                ; turn off fan
G0 X0 Y-4 Z15 F4800 ; move away from printbed

M117 Done
M300 S440 P80 ; beep
M300 S440 P80 ; beep
