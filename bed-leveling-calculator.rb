#!/usr/bin/env ruby
# frozen_string_literal: true

# ---------------------------------------------------------------------------
# Suspension points (X, Y)
# ---------------------------------------------------------------------------
SUSPENSION = [
  [-28.1,  -37.2],
  [290.91, -37.2],
  [125.0,  274.3],
].freeze

# ---------------------------------------------------------------------------
# Mesh layout
# ---------------------------------------------------------------------------
MESH_X = [15.0, 125.0, 230.0].freeze
MESH_Y = [220.0, 115.0, 10.0].freeze   # top row → highest Y

MESH_Z = [
  # x=15    x=125   x=230
   0.203,   0.311,   0.602,   # y=220
   0.102,   0.147,   0.464,   # y=115
  -0.338,  -0.378,   0.009,   # y=10
].freeze

# ---------------------------------------------------------------------------
# Build list of (x, y, z) mesh points
# ---------------------------------------------------------------------------
MESH_POINTS = MESH_Y.each_with_index.flat_map do |y, row|
  MESH_X.each_with_index.map do |x, col|
    [x, y, MESH_Z[row * MESH_X.size + col]]
  end
end.freeze

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Fit a plane z = a*x + b*y + c through exactly 3 points.
# Returns [a, b, c] or nil if points are collinear.
def plane_through_3(p1, p2, p3)
  x1, y1, z1 = p1
  x2, y2, z2 = p2
  x3, y3, z3 = p3

  # Build 3×3 system:  [x y 1] · [a b c]^T = z
  mat = [[x1, y1, 1], [x2, y2, 1], [x3, y3, 1]]
  rhs = [z1, z2, z3]

  det = mat[0][0] * (mat[1][1] * mat[2][2] - mat[1][2] * mat[2][1]) -
        mat[0][1] * (mat[1][0] * mat[2][2] - mat[1][2] * mat[2][0]) +
        mat[0][2] * (mat[1][0] * mat[2][1] - mat[1][1] * mat[2][0])

  return nil if det.abs < 1e-10

  inv = [
    [
      (mat[1][1]*mat[2][2] - mat[1][2]*mat[2][1]) / det,
      (mat[0][2]*mat[2][1] - mat[0][1]*mat[2][2]) / det,
      (mat[0][1]*mat[1][2] - mat[0][2]*mat[1][1]) / det,
    ],
    [
      (mat[1][2]*mat[2][0] - mat[1][0]*mat[2][2]) / det,
      (mat[0][0]*mat[2][2] - mat[0][2]*mat[2][0]) / det,
      (mat[0][2]*mat[1][0] - mat[0][0]*mat[1][2]) / det,
    ],
    [
      (mat[1][0]*mat[2][1] - mat[1][1]*mat[2][0]) / det,
      (mat[0][1]*mat[2][0] - mat[0][0]*mat[2][1]) / det,
      (mat[0][0]*mat[1][1] - mat[0][1]*mat[1][0]) / det,
    ],
  ]

  a = inv[0][0]*rhs[0] + inv[0][1]*rhs[1] + inv[0][2]*rhs[2]
  b = inv[1][0]*rhs[0] + inv[1][1]*rhs[1] + inv[1][2]*rhs[2]
  c = inv[2][0]*rhs[0] + inv[2][1]*rhs[1] + inv[2][2]*rhs[2]
  [a, b, c]
end

def eval_plane(abc, x, y)
  abc[0] * x + abc[1] * y + abc[2]
end

# ---------------------------------------------------------------------------
# Allowed tolerance for slightly negative shim values
# ---------------------------------------------------------------------------
SHIM_NEG_TOLERANCE = -0.025

# ---------------------------------------------------------------------------
# Enumerate all C(9,3) = 84 combinations of mesh points
# ---------------------------------------------------------------------------
indices = (0...MESH_POINTS.size).to_a
combos = indices.combination(3).to_a

results = []

combos.each do |idx_triple|
  p1, p2, p3 = idx_triple.map { |i| MESH_POINTS[i] }

  abc = plane_through_3(p1, p2, p3)
  next unless abc

  # Z is up. The measured surface is Z(x,y) = a*x + b*y + c.
  # Raising suspension point i by delta_i adds a tilt T(x,y) to the bed.
  # T must cancel the existing tilt: T(x,y) = -a*x - b*y + k
  # So delta_i = T(sx_i,sy_i) = k - (a*sx_i + b*sy_i)  (must be >= 0).
  # Minimal k: k = max_i(a*sx_i + b*sy_i)
  # => the suspension point with the largest tilt component gets delta = 0,
  #    all others (lower on the tilted plane) get lifted more.
  a, b, c = abc
  tilt_at_susp = SUSPENSION.map { |sx, sy| a * sx + b * sy }
  k            = tilt_at_susp.max
  susp_adj     = tilt_at_susp.map { |t| k - t }

  next unless susp_adj.all? { |v| v >= -1e-9 }

  # After the adjustment the bed is flat at height (c + k).
  # Shim at each mesh point = how far that point sits below the flat level:
  #   shim = eval_plane(abc, mx, my) - Z_measured
  # Positive: point is below the flat level => needs a physical shim up.
  # Negative: point is above the flat level => slight air gap (within tolerance ok).
  # Reference points yield shim == 0 by construction.
  shims = MESH_POINTS.map do |mx, my, mz|
    eval_plane(abc, mx, my) - mz
  end

  # Validity: shims must be >= SHIM_NEG_TOLERANCE
  next unless shims.all? { |s| s >= SHIM_NEG_TOLERANCE - 1e-9 }

  total_lift = susp_adj.sum + shims.select { |s| s > 0 }.sum

  results << {
    combo:      idx_triple,
    susp_adj:   susp_adj,
    shims:      shims,
    total_lift: total_lift,
    plane:      abc,
  }
end

# ---------------------------------------------------------------------------
# Sort by total lift (lower is better)
# ---------------------------------------------------------------------------
results.sort_by! { |r| r[:total_lift] }

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def fmt(v, width = 8, decimals = 4)
  format("%#{width}.#{decimals}f", v)
end

puts "=" * 72
puts "  PLANE LEVELING — ALL VALID SOLUTIONS (ranked by total lift, ascending)"
puts "=" * 72

if results.empty?
  puts "\nNo valid solutions found."
else
  results.each_with_index do |r, rank|
    puts
    puts "-" * 72
    combo_labels = r[:combo].map do |i|
      row, col = i.divmod(MESH_X.size)
      "MP(x=#{MESH_X[col].to_i},y=#{MESH_Y[row].to_i})"
    end
    puts "  Rank #{rank + 1}  |  Reference points: #{combo_labels.join(', ')}"
    puts "  Total lift score: #{fmt(r[:total_lift], 0, 4)}"
    puts

    puts "  Suspension point Z adjustments:"
    SUSPENSION.each_with_index do |(sx, sy), i|
      puts "    S#{i + 1} (#{sx}, #{sy})  =>  +#{fmt(r[:susp_adj][i])}"
    end

    puts
    puts "  Shim distances at mesh points (+ = shim needed, - = air gap):"
    header = "    " + MESH_X.map { |x| format("   x=%-5g", x) }.join
    puts header
    MESH_Y.each_with_index do |y, row|
      row_vals = MESH_X.size.times.map { |col| r[:shims][row * MESH_X.size + col] }
      puts "    y=#{format('%-5g', y)}  " + row_vals.map { |s| fmt(s) }.join("  ")
    end
  end
end

puts
puts "=" * 72
puts "  Total valid solutions: #{results.size}  (out of #{combos.size} combinations tried)"
puts "=" * 72
