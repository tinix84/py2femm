"""Unit tests for multi-zone heatsink model (no FEMM required)."""
from __future__ import annotations

import sys
from pathlib import Path

_examples_dir = str(Path(__file__).resolve().parent.parent / "examples" / "heatflow" / "heatsink")
if _examples_dir not in sys.path:
    sys.path.insert(0, _examples_dir)

import pytest
from heatsink_multizone import Zone, Chip, MultiZoneConfig, validate_config


def test_valid_config():
    """A well-formed 3-zone 2-chip config passes validation."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=60, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=60, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=5),
            Zone(x_start=100, x_end=180, material="Copper", kx=385, ky=385, h_conv=50),
        ],
        chips=[
            Chip(name="ChipA", x_center=30, width=20, power=5.0),
            Chip(name="ChipB", x_center=140, width=30, power=15.0),
        ],
        base_w=180, base_h=10,
    )
    validate_config(cfg)  # should not raise


def test_zones_gap_rejected():
    """Zones with a gap between them should fail validation."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=50, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=60, x_end=180, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=30, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="contiguous"):
        validate_config(cfg)


def test_zones_wrong_start_rejected():
    """First zone must start at 0."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=10, x_end=180, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=90, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="start at 0"):
        validate_config(cfg)


def test_zones_wrong_end_rejected():
    """Last zone must end at base_w."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=50, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="end at base_w"):
        validate_config(cfg)


def test_chip_outside_base_rejected():
    """Chip contact extending beyond base_w should fail."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=180, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=175, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="outside"):
        validate_config(cfg)
