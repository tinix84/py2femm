"""Multi-Zone Heat Sink Thermal Analysis.

Demonstrates a heat sink with multiple thermal zones along the x-axis,
each with its own material (e.g., aluminum, copper) and convection
coefficient (representing different fin densities or a mounting bracket).

Compares a uniform baseline against an optimized multi-zone layout to
show the cost/performance tradeoff of using copper inserts and varied
fin density.

Usage:
    python examples/heatflow/heatsink/heatsink_multizone.py
    python examples/heatflow/heatsink/heatsink_multizone.py --start-server
    python examples/heatflow/heatsink/heatsink_multizone.py --no-plot

See GitHub issue #1 for motivation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from py2femm.client import FemmClient
from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Node, Line
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial


# ═══════════════════════════════════════════════════════════════════
# Configuration dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Zone:
    """A rectangular thermal zone spanning the full base height."""
    x_start: float      # left edge [mm]
    x_end: float         # right edge [mm]
    material: str        # e.g. "Aluminum", "Copper"
    kx: float            # thermal conductivity x [W/(m·K)]
    ky: float            # thermal conductivity y [W/(m·K)]
    h_conv: float        # convection coefficient on top surface [W/(m²·K)]


@dataclass
class Chip:
    """Heat source placed on the bottom surface."""
    name: str            # e.g. "ChipA"
    x_center: float      # center position [mm]
    width: float         # contact width [mm]
    power: float         # dissipated power [W]


@dataclass
class MultiZoneConfig:
    """Multi-zone heat sink configuration."""
    zones: list[Zone]
    chips: list[Chip]
    base_w: float        # total width [mm]
    base_h: float        # total height [mm]
    depth: float = 100.0     # extrusion depth [mm]
    t_ambient: float = 300.0  # ambient temperature [K]


def validate_config(cfg: MultiZoneConfig) -> None:
    """Validate that zones tile [0, base_w] and chips fit within the base."""
    if not cfg.zones:
        raise ValueError("At least one zone required")
    if abs(cfg.zones[0].x_start) > 1e-6:
        raise ValueError(f"First zone must start at 0, got {cfg.zones[0].x_start}")
    if abs(cfg.zones[-1].x_end - cfg.base_w) > 1e-6:
        raise ValueError(f"Last zone must end at base_w={cfg.base_w}, got {cfg.zones[-1].x_end}")
    for i in range(len(cfg.zones) - 1):
        if abs(cfg.zones[i].x_end - cfg.zones[i + 1].x_start) > 1e-6:
            raise ValueError(
                f"Zones must be contiguous: zone {i} ends at {cfg.zones[i].x_end}, "
                f"zone {i + 1} starts at {cfg.zones[i + 1].x_start}"
            )
    for chip in cfg.chips:
        left = chip.x_center - chip.width / 2
        right = chip.x_center + chip.width / 2
        if left < -1e-6 or right > cfg.base_w + 1e-6:
            raise ValueError(f"Chip '{chip.name}' contact [{left}, {right}] outside base [0, {cfg.base_w}]")


# ═══════════════════════════════════════════════════════════════════
# Geometry builder
# ═══════════════════════════════════════════════════════════════════

def build_geometry(cfg: MultiZoneConfig) -> tuple[Geometry, list[Node], list[Line], list[Line]]:
    """Build the multi-zone rectangular geometry with vertical partitions.

    Returns:
        geo: Geometry object with all nodes and lines
        bottom_nodes: sorted bottom-edge nodes (for BC assignment)
        top_segments: top-edge Line per zone (for per-zone convection BC)
        internal_lines: vertical partition lines at zone boundaries
    """
    # Collect all unique x-coordinates on the bottom edge
    bottom_x_set: set[float] = {0.0, cfg.base_w}
    for zone in cfg.zones:
        bottom_x_set.add(zone.x_start)
        bottom_x_set.add(zone.x_end)
    for chip in cfg.chips:
        bottom_x_set.add(chip.x_center - chip.width / 2)
        bottom_x_set.add(chip.x_center + chip.width / 2)

    # Deduplicate with tolerance
    bottom_x_sorted = sorted(bottom_x_set)
    deduped_x: list[float] = [bottom_x_sorted[0]]
    for x in bottom_x_sorted[1:]:
        if abs(x - deduped_x[-1]) > 1e-6:
            deduped_x.append(x)
    bottom_x_sorted = deduped_x

    # Top edge x-coordinates: only at zone boundaries
    top_x_sorted = sorted(set(z.x_start for z in cfg.zones) | {cfg.zones[-1].x_end})

    # Create nodes
    bottom_nodes = [Node(x, 0) for x in bottom_x_sorted]
    top_nodes = [Node(x, cfg.base_h) for x in top_x_sorted]

    # Build node lookup for line creation
    all_nodes: list[Node] = []
    node_map: dict[tuple[float, float], Node] = {}
    for n in bottom_nodes + top_nodes:
        key = (round(n.x, 6), round(n.y, 6))
        if key not in node_map:
            node_map[key] = n
            all_nodes.append(n)

    def get_node(x: float, y: float) -> Node:
        key = (round(x, 6), round(y, 6))
        return node_map[key]

    # Lines: bottom edge segments
    all_lines: list[Line] = []
    for i in range(len(bottom_x_sorted) - 1):
        all_lines.append(Line(get_node(bottom_x_sorted[i], 0), get_node(bottom_x_sorted[i + 1], 0)))

    # Lines: top edge segments (one per zone)
    top_segments: list[Line] = []
    for zone in cfg.zones:
        seg = Line(get_node(zone.x_start, cfg.base_h), get_node(zone.x_end, cfg.base_h))
        top_segments.append(seg)
        all_lines.append(seg)

    # Lines: left and right side walls
    all_lines.append(Line(get_node(0, 0), get_node(0, cfg.base_h)))
    all_lines.append(Line(get_node(cfg.base_w, 0), get_node(cfg.base_w, cfg.base_h)))

    # Lines: internal vertical partitions at zone boundaries (excluding x=0 and x=base_w)
    internal_lines: list[Line] = []
    for i in range(len(cfg.zones) - 1):
        x_b = cfg.zones[i].x_end
        line = Line(get_node(x_b, 0), get_node(x_b, cfg.base_h))
        internal_lines.append(line)
        all_lines.append(line)

    geo = Geometry()
    geo.nodes = all_nodes
    geo.lines = all_lines

    return geo, bottom_nodes, top_segments, internal_lines
