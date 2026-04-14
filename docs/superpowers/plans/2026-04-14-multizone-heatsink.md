# Multi-Zone Heatsink Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new example (`heatsink_multizone.py`) that builds a multi-zone heat sink FEMM model where each zone has its own material and convection coefficient, then compares a uniform baseline against an optimized multi-zone layout.

**Architecture:** A single module with `Zone`, `Chip`, `MultiZoneConfig` dataclasses, a geometry builder that creates vertical partition lines at zone boundaries, a FEMM problem builder that assigns per-zone materials/BCs, and a comparison runner that evaluates two scenarios side-by-side. Follows the same patterns as `heatsink_optimize.py` (dataclass config, `build_model()` returns Lua string, `parse_results()` extracts key-value pairs).

**Tech Stack:** Python 3.10+, py2femm (FemmProblem, FemmClient, Geometry, Node, Line), HeatFlowMaterial, HeatFlowConvection, HeatFlowHeatFlux, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `examples/heatflow/heatsink/heatsink_multizone.py` | Create | Zone, Chip, MultiZoneConfig dataclasses; validate_config(); build_geometry(); build_model(); parse_results(); compare_scenarios(); main() |
| `tests/test_multizone.py` | Create | Unit tests: config validation, geometry node/line counts, Lua output checks, material dedup, BC assignment |

---

### Task 1: Dataclasses and Config Validation

**Files:**
- Create: `examples/heatflow/heatsink/heatsink_multizone.py`
- Create: `tests/test_multizone.py`

- [ ] **Step 1: Write failing tests for dataclasses and validation**

Create `tests/test_multizone.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_multizone.py -v`
Expected: FAIL — `heatsink_multizone` module not found

- [ ] **Step 3: Implement dataclasses and validate_config**

Create `examples/heatflow/heatsink/heatsink_multizone.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_multizone.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_multizone.py tests/test_multizone.py
git commit -m "feat: add multizone heatsink dataclasses and config validation"
```

---

### Task 2: Geometry Builder

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_multizone.py`
- Modify: `tests/test_multizone.py`

- [ ] **Step 1: Write failing tests for geometry**

Add to `tests/test_multizone.py`:

```python
from heatsink_multizone import build_geometry


def _make_3zone_2chip_config() -> MultiZoneConfig:
    """Standard 3-zone 2-chip config for tests."""
    return MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=60, material="Aluminum", kx=200, ky=200, h_conv=15),
            Zone(x_start=60, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=5),
            Zone(x_start=100, x_end=180, material="Copper", kx=385, ky=385, h_conv=50),
        ],
        chips=[
            Chip(name="ChipA", x_center=30, width=20, power=5.0),
            Chip(name="ChipB", x_center=140, width=30, power=15.0),
        ],
        base_w=180, base_h=10,
    )


def test_geometry_node_count():
    """3 zones + 2 chips: expect correct node count."""
    cfg = _make_3zone_2chip_config()
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    # Bottom edge nodes: 0, 20, 40, 60, 100, 125, 155, 180 = 8 unique x-values
    # (zone boundaries: 0, 60, 100, 180; chip edges: 20, 40, 125, 155)
    # Top edge nodes: 0, 60, 100, 180 = 4 x-values at y=base_h
    # Total unique = 8 + 4 = 12
    assert len(geo.nodes) == 12


def test_geometry_internal_partition_count():
    """3 zones = 2 internal partition lines."""
    cfg = _make_3zone_2chip_config()
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    assert len(internal_lines) == 2


def test_geometry_top_segments_count():
    """3 zones = 3 top segments."""
    cfg = _make_3zone_2chip_config()
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    assert len(top_segments) == 3


def test_chip_at_zone_boundary_no_duplicate():
    """Chip edge coinciding with zone boundary should not create duplicate nodes."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=50, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=50, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=50, width=20, power=5.0)],
        base_w=100, base_h=10,
    )
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    # Bottom x-values: 0, 40, 50, 60, 100 (50 is both zone boundary and near chip)
    bottom_xs = sorted(set(round(n.x, 6) for n in bottom_nodes))
    assert len(bottom_xs) == len(bottom_nodes), "Duplicate bottom nodes detected"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_multizone.py::test_geometry_node_count tests/test_multizone.py::test_geometry_internal_partition_count -v`
Expected: FAIL — `build_geometry` not found

- [ ] **Step 3: Implement build_geometry**

Add to `examples/heatflow/heatsink/heatsink_multizone.py` after `validate_config`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_multizone.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_multizone.py tests/test_multizone.py
git commit -m "feat: add multi-zone geometry builder with vertical partitions"
```

---

### Task 3: FEMM Problem Builder (build_model)

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_multizone.py`
- Modify: `tests/test_multizone.py`

- [ ] **Step 1: Write failing tests for Lua output**

Add to `tests/test_multizone.py`:

```python
from heatsink_multizone import build_model


def test_build_model_material_dedup():
    """Two zones with same material name should produce only one hi_addmaterial call."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    # Aluminum appears in zone 0 and 1, Copper in zone 2 → 2 hi_addmaterial calls
    assert lua.count("hi_addmaterial") == 2


def test_build_model_block_labels_per_zone():
    """Each zone gets its own hi_addblocklabel call."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert lua.count("hi_addblocklabel") == 3


def test_build_model_per_zone_convection():
    """Each zone's top segment gets a distinct convection BC."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    # 3 zones with different h values → 3 hi_addboundprop calls for convection
    # Plus 2 heat flux BCs for chips → total 5 hi_addboundprop
    assert lua.count("hi_addboundprop") == 5


def test_build_model_chip_heat_flux():
    """Each chip gets a heat flux BC."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "Heat_ChipA" in lua
    assert "Heat_ChipB" in lua


def test_build_model_no_table_indexing():
    """FEMM Lua 4.0: no table indexing [1] allowed."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "[1]" not in lua


def test_build_model_has_sentinel():
    """Lua must contain PY2FEMM_DONE sentinel."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "PY2FEMM_DONE" in lua


def test_build_model_ends_with_quit():
    """Lua must end with quit()."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    lines = lua.strip().splitlines()
    assert lines[-1].strip() == "quit()"


def test_build_model_writes_chip_temperatures():
    """Lua must write T_ChipA_K and T_ChipB_K to file_out."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "T_ChipA_K" in lua
    assert "T_ChipB_K" in lua


def test_build_model_writes_zone_temperatures():
    """Lua must write per-zone average temperatures."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "T_avg_zone_0_K" in lua
    assert "T_avg_zone_1_K" in lua
    assert "T_avg_zone_2_K" in lua
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_multizone.py::test_build_model_material_dedup -v`
Expected: FAIL — `build_model` not found

- [ ] **Step 3: Implement build_model**

Add to `examples/heatflow/heatsink/heatsink_multizone.py` after `build_geometry`:

```python
# ═══════════════════════════════════════════════════════════════════
# FEMM model builder
# ═══════════════════════════════════════════════════════════════════

def build_model(cfg: MultiZoneConfig) -> str:
    """Build a multi-zone FEMM heat flow model, return the Lua script."""
    validate_config(cfg)
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)

    problem = FemmProblem(out_file="multizone_results.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS, type="planar",
        precision=1e-8, depth=cfg.depth, minangle=30,
    )
    problem.create_geometry(geo)

    # --- Materials (deduplicated by name) ---
    added_materials: dict[str, HeatFlowMaterial] = {}
    for zone in cfg.zones:
        if zone.material not in added_materials:
            mat = HeatFlowMaterial(
                material_name=zone.material, kx=zone.kx, ky=zone.ky, qv=0.0, kt=0.0,
            )
            problem.add_material(mat)
            added_materials[zone.material] = mat

    # Block label per zone
    for i, zone in enumerate(cfg.zones):
        label_x = (zone.x_start + zone.x_end) / 2
        label_y = cfg.base_h / 2
        problem.define_block_label(Node(label_x, label_y), added_materials[zone.material])

    # --- Boundary conditions ---
    # Per-chip heat flux on bottom surface
    chip_contact_ranges: list[tuple[float, float]] = []
    for chip in cfg.chips:
        x_left = chip.x_center - chip.width / 2
        x_right = chip.x_center + chip.width / 2
        chip_contact_ranges.append((x_left, x_right))
        qs = chip.power / (chip.width * cfg.depth * 1e-6)
        bc = HeatFlowHeatFlux(name=f"Heat_{chip.name}", qs=-qs)
        bc.Tset = 0; bc.Tinf = 0; bc.h = 0; bc.beta = 0
        problem.add_boundary(bc)
        seg_mid_x = (x_left + x_right) / 2
        problem.set_boundary_definition_segment(Node(seg_mid_x, 0), bc, elementsize=1)

    # Per-zone convection on top surface
    for i, (zone, top_seg) in enumerate(zip(cfg.zones, top_segments)):
        conv = HeatFlowConvection(name=f"Conv_zone_{i}", Tinf=cfg.t_ambient, h=zone.h_conv)
        conv.Tset = 0; conv.qs = 0; conv.beta = 0
        problem.add_boundary(conv)
        problem.set_boundary_definition_segment(top_seg.selection_point(), conv, elementsize=1)

    # Side walls and bottom non-contact segments: leave unassigned (insulated)
    # Internal partition lines: leave unassigned (perfect thermal contact)

    # --- Analysis + post-processing ---
    problem.make_analysis("planar")

    # Chip temperatures
    for chip in cfg.chips:
        problem.lua_script.append(f"T_{chip.name} = ho_getpointvalues({chip.x_center}, 0)")
        problem.lua_script.append(
            f'write(file_out, "T_{chip.name}_K = ", T_{chip.name}, "\\n")'
        )

    # Per-zone average temperature
    for i, zone in enumerate(cfg.zones):
        label_x = (zone.x_start + zone.x_end) / 2
        label_y = cfg.base_h / 2
        problem.lua_script.append(f"ho_selectblock({label_x}, {label_y})")
        problem.lua_script.append(f"T_avg_z{i} = ho_blockintegral(0)")
        problem.lua_script.append("ho_clearblock()")
        problem.lua_script.append(
            f'write(file_out, "T_avg_zone_{i}_K = ", T_avg_z{i}, "\\n")'
        )

    problem.close()
    return "\n".join(problem.lua_script)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_multizone.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_multizone.py tests/test_multizone.py
git commit -m "feat: add multi-zone FEMM model builder with per-zone materials and BCs"
```

---

### Task 4: Parse Results and Comparison Logic

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_multizone.py`
- Modify: `tests/test_multizone.py`

- [ ] **Step 1: Write failing tests for parse_results and compare**

Add to `tests/test_multizone.py`:

```python
from heatsink_multizone import parse_results, format_comparison


def test_parse_results():
    """parse_results extracts key=value pairs from CSV output."""
    raw = (
        "T_ChipA_K = 345.2\n"
        "T_ChipB_K = 378.4\n"
        "T_avg_zone_0_K = 340.1\n"
        "T_avg_zone_1_K = 335.8\n"
        "T_avg_zone_2_K = 355.3\n"
        "PY2FEMM_DONE\n"
    )
    results = parse_results(raw)
    assert results["T_ChipA_K"] == pytest.approx(345.2)
    assert results["T_ChipB_K"] == pytest.approx(378.4)
    assert results["T_avg_zone_0_K"] == pytest.approx(340.1)


def test_format_comparison():
    """format_comparison produces a string with chip temperatures and R_th."""
    results_a = {"T_ChipA_K": 345.0, "T_ChipB_K": 370.0}
    results_b = {"T_ChipA_K": 348.0, "T_ChipB_K": 361.0}
    cfg = _make_3zone_2chip_config()
    text = format_comparison(cfg, results_a, results_b)
    assert "ChipA" in text
    assert "ChipB" in text
    assert "R_th" in text
    assert "Uniform" in text
    assert "Multi-zone" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_multizone.py::test_parse_results tests/test_multizone.py::test_format_comparison -v`
Expected: FAIL — functions not found

- [ ] **Step 3: Implement parse_results and format_comparison**

Add to `examples/heatflow/heatsink/heatsink_multizone.py` after `build_model`:

```python
# ═══════════════════════════════════════════════════════════════════
# Results parsing and comparison
# ═══════════════════════════════════════════════════════════════════

def parse_results(raw_csv: str) -> dict[str, float]:
    """Parse key=value pairs from FEMM CSV output."""
    results: dict[str, float] = {}
    for line in raw_csv.strip().splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().rstrip(",")
        try:
            results[key] = float(val)
        except ValueError:
            pass
    return results


def format_comparison(
    cfg: MultiZoneConfig,
    results_uniform: dict[str, float],
    results_multizone: dict[str, float],
) -> str:
    """Format a side-by-side comparison table."""
    lines: list[str] = []
    header = f"{'Metric':<25} {'Uniform':>12} {'Multi-zone':>12} {'Delta':>12}"
    lines.append(header)
    lines.append("-" * len(header))

    for chip in cfg.chips:
        key = f"T_{chip.name}_K"
        t_u = results_uniform.get(key, float("nan"))
        t_m = results_multizone.get(key, float("nan"))
        lines.append(f"{'T_' + chip.name + ' [K]':<25} {t_u:>12.1f} {t_m:>12.1f} {t_m - t_u:>+12.1f}")

        r_u = (t_u - cfg.t_ambient) / chip.power
        r_m = (t_m - cfg.t_ambient) / chip.power
        lines.append(f"{'R_th_' + chip.name + ' [K/W]':<25} {r_u:>12.2f} {r_m:>12.2f} {r_m - r_u:>+12.2f}")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_multizone.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_multizone.py tests/test_multizone.py
git commit -m "feat: add result parsing and comparison formatting for multizone"
```

---

### Task 5: Server Utilities and Scenario Definitions

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_multizone.py`

- [ ] **Step 1: Add server management and scenario factory functions**

Add to `examples/heatflow/heatsink/heatsink_multizone.py` after the imports (before the dataclass section):

```python
# ═══════════════════════════════════════════════════════════════════
# Server management
# ═══════════════════════════════════════════════════════════════════

HEALTH_URL = "http://localhost:8082/api/v1/health"


def server_is_healthy() -> bool:
    try:
        resp = urllib.request.urlopen(HEALTH_URL, timeout=2)
        return json.loads(resp.read()).get("status") == "ok"
    except Exception:
        return False


def start_server() -> None:
    if server_is_healthy():
        print("[server] Already running.")
        return
    repo = Path(__file__).resolve().parent
    while repo.name and not (repo / "start_femm_server.bat").exists():
        repo = repo.parent
    bat = repo / "start_femm_server.bat"
    assert bat.exists(), "start_femm_server.bat not found"
    print(f"[server] Launching {bat}")
    subprocess.Popen(
        ["cmd", "/c", str(bat)], cwd=str(repo),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    for _ in range(30):
        time.sleep(1)
        if server_is_healthy():
            print("[server] Ready.")
            return
    raise RuntimeError("Server did not start within 30s")
```

Then add the scenario definitions after `format_comparison`:

```python
# ═══════════════════════════════════════════════════════════════════
# Predefined scenarios
# ═══════════════════════════════════════════════════════════════════

CHIPS = [
    Chip(name="ChipA", x_center=30, width=20, power=5.0),
    Chip(name="ChipB", x_center=140, width=30, power=15.0),
]


def make_uniform_config() -> MultiZoneConfig:
    """Scenario A: uniform aluminum, h=25 everywhere."""
    return MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=60, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=60, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=100, x_end=180, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=CHIPS, base_w=180, base_h=10,
    )


def make_multizone_config() -> MultiZoneConfig:
    """Scenario B: optimized multi-zone with copper insert."""
    return MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=60, material="Aluminum", kx=200, ky=200, h_conv=15),
            Zone(x_start=60, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=5),
            Zone(x_start=100, x_end=180, material="Copper", kx=385, ky=385, h_conv=50),
        ],
        chips=CHIPS, base_w=180, base_h=10,
    )
```

- [ ] **Step 2: Verify no regressions**

Run: `python -m pytest tests/test_multizone.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_multizone.py
git commit -m "feat: add server utils and predefined multizone scenarios"
```

---

### Task 6: Main Entry Point

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_multizone.py`

- [ ] **Step 1: Implement main() with scenario runner and comparison**

Add to the end of `examples/heatflow/heatsink/heatsink_multizone.py`:

```python
# ═══════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════

def run_scenario(cfg: MultiZoneConfig, label: str) -> dict[str, float]:
    """Build model, submit to FEMM, return parsed results."""
    print(f"\n--- {label} ---")
    lua = build_model(cfg)
    print(f"  Lua: {len(lua)} chars, {lua.count(chr(10))} lines")

    client = FemmClient(mode="remote", url="http://localhost:8082")
    result = client.run(lua, timeout=120)
    assert result.error is None, f"FEMM failed: {result.error}"
    assert result.csv_data, "No CSV data returned"

    parsed = parse_results(result.csv_data)
    for k, v in sorted(parsed.items()):
        print(f"  {k} = {v:.2f}")
    return parsed


def main():
    parser = argparse.ArgumentParser(description="Multi-zone heat sink comparison")
    parser.add_argument("--start-server", action="store_true",
                        help="Launch start_femm_server.bat before running")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip matplotlib plots")
    args = parser.parse_args()

    if args.start_server:
        start_server()
    else:
        assert server_is_healthy(), (
            "py2femm server not running on localhost:8082.\n"
            "  Start it with: start_femm_server.bat\n"
            "  Or pass --start-server to this script."
        )
        print("[server] OK")

    cfg_uniform = make_uniform_config()
    cfg_multizone = make_multizone_config()

    results_uniform = run_scenario(cfg_uniform, "Scenario A: Uniform")
    results_multizone = run_scenario(cfg_multizone, "Scenario B: Multi-zone")

    print("\n" + "=" * 65)
    print("COMPARISON")
    print("=" * 65)
    print(format_comparison(cfg_uniform, results_uniform, results_multizone))
    print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify no regressions**

Run: `python -m pytest tests/test_multizone.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_multizone.py
git commit -m "feat: add main entry point with scenario comparison runner"
```

---

### Task 7: Full Test Suite and Lint Check

**Files:**
- No code changes — validation only

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests pass (both new multizone tests and all existing tests)

- [ ] **Step 2: Run ruff linter**

Run: `ruff check examples/heatflow/heatsink/heatsink_multizone.py tests/test_multizone.py`
Expected: No errors

- [ ] **Step 3: Fix any issues, commit if needed**

Only if previous steps revealed lint or test issues.
