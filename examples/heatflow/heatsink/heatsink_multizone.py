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
