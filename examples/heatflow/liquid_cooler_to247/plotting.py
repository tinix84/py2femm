"""Parse and plot temperature grids dumped by circular/rectangular builders."""
from __future__ import annotations

import re


def parse_temperature_grid(csv_text: str):
    """Extract the T(x,y) grid from a circular/rectangular CSV result.

    The builders emit a `GRID nx=.. ny=.. xmin=.. xmax=.. ymin=.. ymax=..` header
    followed by `T[i,j] = value` rows. Returns (T, x_edges, y_edges) with T[ny,nx].
    """
    import numpy as np

    m = re.search(
        r"GRID\s+nx=(\d+)\s+ny=(\d+)\s+xmin=([\d.eE+-]+)\s+xmax=([\d.eE+-]+)"
        r"\s+ymin=([\d.eE+-]+)\s+ymax=([\d.eE+-]+)",
        csv_text,
    )
    if m is None:
        raise ValueError("GRID header not found in CSV output")
    nx, ny = int(m.group(1)), int(m.group(2))
    x_min, x_max = float(m.group(3)), float(m.group(4))
    y_min, y_max = float(m.group(5)), float(m.group(6))

    T = np.full((ny, nx), float("nan"))
    for m in re.finditer(r"T\[(\d+),(\d+)\]\s*=\s*([\d.eE+-]+)", csv_text):
        i, j, v = int(m.group(1)), int(m.group(2)), float(m.group(3))
        if 0 <= i < nx and 0 <= j < ny:
            T[j, i] = v
    x = np.linspace(x_min, x_max, nx)
    y = np.linspace(y_min, y_max, ny)
    return T, x, y


def plot_temperature_field(csv_texts: list[str], titles: list[str],
                           figsize=(13, 5), levels: int = 20):
    """Side-by-side filled-contour plots of T(x,y) for each CSV."""
    import matplotlib.pyplot as plt
    n = len(csv_texts)
    fig, axes = plt.subplots(1, n, figsize=figsize, squeeze=False)

    # Shared color scale across both
    Ts = [parse_temperature_grid(t) for t in csv_texts]
    vmin = min(T[~(T != T)].min() if False else float("inf") for T, _, _ in Ts)
    import numpy as np
    vmin = min(np.nanmin(T) for T, _, _ in Ts)
    vmax = max(np.nanmax(T) for T, _, _ in Ts)

    for ax, (T, x, y), title in zip(axes[0], Ts, titles):
        cs = ax.contourf(x, y, T, levels=levels, vmin=vmin, vmax=vmax, cmap="inferno")
        ax.set_aspect("equal")
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
        ax.set_title(title)
        fig.colorbar(cs, ax=ax, label="T [K]")
    fig.tight_layout()
    return fig
