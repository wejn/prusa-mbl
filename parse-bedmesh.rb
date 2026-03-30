#!/usr/bin/env ruby

files = Dir.glob("gcode_G29_P10_V4_*")

points = []

# Extract data
files.each do |file|
  File.foreach(file) do |line|
    if line =~ /Bed X:\s*([-\d.]+)\s*Y:\s*([-\d.]+)\s*Z:\s*([-\d.]+)/
      x = $1.to_f
      y = $2.to_f
      z = $3.to_f
      points << [x, y, z]
    end
  end
end

# Get unique sorted axes
xs = points.map { |p| p[0] }.uniq.sort
ys = points.map { |p| p[1] }.uniq.sort.reverse

# Build lookup hash
grid = {}
points.each do |x, y, z|
  grid[[x, y]] = z
end

# Header
header = xs.map { |x| "x=#{x.to_i}".ljust(8) }.join
puts "MESH_Z = ["
puts "  # #{header}(for each y row)"

# Rows
ys.each do |y|
  row = xs.map do |x|
    val = grid[[x, y]] || 0.0
    "% .3f" % val
  end.join(",  ")

  puts "  #{row},  # y=#{y.to_i}"
end

puts "].freeze"
