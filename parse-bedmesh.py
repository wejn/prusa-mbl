#!/usr/bin/env python3

import glob
import re
from collections import defaultdict

pattern = re.compile(r"Bed X:\s*([-\d.]+)\s*Y:\s*([-\d.]+)\s*Z:\s*([-\d.]+)")

points = []

# Read all matching files
for filename in glob.glob("gcode_G29_P10_V4_*"):
    with open(filename, "r") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                x = float(m.group(1))
                y = float(m.group(2))
                z = float(m.group(3))
                points.append((x, y, z))

# Collect sorted unique axes
xs = sorted(set(p[0] for p in points))
ys = reversed(sorted(set(p[1] for p in points)))

# Build lookup
grid = {(x, y): z for (x, y, z) in points}

# Header
header = "".join(f"x={int(x):<6}" for x in xs)

print("MESH_Z = [")
print(f"  # {header}(for each y row)")

# Rows
for y in ys:
    row_vals = []
    for x in xs:
        z = grid.get((x, y), 0.0)
        row_vals.append(f"{z: .3f}")
    row_str = ",  ".join(row_vals)
    print(f"  {row_str},  # y={int(y)}")

print("].freeze")
