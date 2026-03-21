"""Bed mesh visualizer."""

import re
import sys
import numpy as np
import matplotlib.pyplot as plt

from matplotlib import cm
from matplotlib.colors import TwoSlopeNorm
from mpl_toolkits.mplot3d import proj3d

# pylint: disable=too-many-locals,invalid-name


def parse_bed_mesh(filepath: str) -> tuple[np.ndarray, tuple, tuple]:
    """
    Parses bed mesh -- the output of "G29 T".
    Returns (grid, (xmin, xmax), (ymin, ymax)).
    """
    with open(filepath, encoding='utf-8') as f:
        text = f.read()

    coord_pattern = re.compile(r'\(\s*(\d+),\s*(\d+)\)')
    coords = coord_pattern.findall(text)
    x_min, y_max = int(coords[0][0]), int(coords[0][1])
    x_max, _     = int(coords[1][0]), int(coords[1][1])
    _,     y_min = int(coords[2][0]), int(coords[2][1])

    row_pattern = re.compile(r'^\s*(\d+)\s*\|(.+)$', re.MULTILINE)
    rows = {}
    for match in row_pattern.finditer(text):
        row_idx = int(match.group(1))
        raw = match.group(2).replace('[', '').replace(']', '')
        values = [float(v) for v in re.findall(r'[+-]?\d+\.\d+', raw)]
        if values:
            rows[row_idx] = values

    sorted_rows = sorted(rows.keys())
    grid = np.array([rows[i] for i in sorted_rows])

    return grid, (x_min, x_max), (y_min, y_max)


def plot_bed_mesh(filepath: str) -> None:
    """
    Plots (visualizes) the bed mesh from *filepath*.
    """
    grid, (x_min, x_max), (y_min, y_max) = parse_bed_mesh(filepath)

    n_y, n_x = grid.shape
    x = np.linspace(x_min, x_max, n_x)
    y = np.linspace(y_min, y_max, n_y)
    X, Y = np.meshgrid(x, y)

    norm = TwoSlopeNorm(vmin=grid.min(), vcenter=0, vmax=grid.max())
    colors = cm.RdYlBu(norm(grid))  # pylint: disable=no-member

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.plot_surface(
        X, Y, grid,
        facecolors=colors,
        rstride=1, cstride=1,
        linewidth=0.3,
        edgecolor='k',
        alpha=0.95,
        antialiased=True,
    )

    z_range = grid.max() - grid.min()
    xy_range = max(x_max - x_min, y_max - y_min)
    ax.set_box_aspect([
        (x_max - x_min) / xy_range,
        (y_max - y_min) / xy_range,
        z_range / xy_range * 50,  # vertical exaggeration
    ])

    mappable = cm.ScalarMappable(cmap='RdYlBu', norm=norm)
    mappable.set_array(grid)
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.5, aspect=12, pad=0.1)
    cbar.set_label('Z offset (mm)', fontsize=11)

    ax.set_xlabel('X (mm)', labelpad=10)
    ax.set_ylabel('Y (mm)', labelpad=10)
    ax.set_zlabel('Z offset (mm)', labelpad=10)
    ax.set_title('Bed Topography', fontsize=14, fontweight='bold')
    ax.view_init(elev=30, azim=-60)

    plt.tight_layout()

    def _on_motion(event):
        """
        Mouse motion tracker.
        """
        if event.inaxes is not ax:
            fig.canvas.toolbar.set_message('')
            return
        min_dist = float('inf')
        best = None
        for iy in range(n_y):
            for ix in range(n_x):
                x2, y2, _ = proj3d.proj_transform(X[iy, ix], Y[iy, ix], grid[iy, ix], ax.get_proj())
                if event.xdata is None or event.ydata is None:
                    return
                dist = (x2 - event.xdata) ** 2 + (y2 - event.ydata) ** 2
                if dist < min_dist:
                    min_dist = dist
                    best = (X[iy, ix], Y[iy, ix], grid[iy, ix])
        if best and min_dist < 0.01:
            fig.canvas.toolbar.set_message(
                f'X: {best[0]:.0f} mm  Y: {best[1]:.0f} mm  Z: {best[2]:+.3f} mm'
            )
        else:
            fig.canvas.toolbar.set_message('')

    fig.canvas.mpl_connect('motion_notify_event', _on_motion)

    plt.show()


def main(argv):
    """
    The main source of pain.
    """
    if len(argv) != 2:
        print("Usage: bedviz.py <g29_t_mesh.txt>")
        return 1
    plot_bed_mesh(argv[1])
    return 0

if __name__ == '__main__':
    main(sys.argv)
