# Heatsink Parametric Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the baseline heatsink thermal model (BC bug, missing bitmap capture) and build a full parametric study module using square-wave fin parametrization with a 360-config factorial sweep.

**Architecture:** Two-layer design — `heatsink_tutorial.py` is the shared backend (geometry, FEMM problem, parsing, server utils) and `heatsink_parametric.py` is the new parametric engine (config dataclass, sweep grid, FEMM builder, plotting). Two notebooks consume these modules: `heatsink_baseline.ipynb` (fixed tutorial reproduction) and `heatsink_parametric.ipynb` (full sweep study).

**Tech Stack:** Python 3.11+, py2femm (FemmProblem, FemmClient), pandas, numpy, matplotlib, dataclasses

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `examples/heatflow/heatsink/heatsink_tutorial.py` | Modify | Fix BC, add bitmap Lua, add `load_femm_bitmap()`, remove parametric sweep (section 9) |
| `examples/heatflow/heatsink/heatsink_parametric.py` | Create | HeatsinkConfig, is_valid, build_sweep_grid, build_femm_problem, run_sweep, all plotting |
| `examples/heatflow/heatsink/heatsink_baseline.ipynb` | Create | 6-cell notebook: fixed tutorial reproduction with FEMM bitmap |
| `examples/heatflow/heatsink/heatsink_parametric.ipynb` | Create | 9-cell notebook: full parametric study |
| `tests/test_heatsink_parametric.py` | Create | Unit tests for HeatsinkConfig, is_valid, build_sweep_grid, Lua output |
| `tests/test_heatsink_tutorial_bc.py` | Create | Regression test verifying bottom segments are insulated |

---

### Task 1: Fix BC Assignment in heatsink_tutorial.py

The current code applies convection to ALL segments except the contact patch (index 1). Bottom segments at y=0 flanking the contact (indices 0 and 2) should be **insulated** (no BC assigned = zero flux in FEMM). This causes T_avg ≈ 334K instead of the expected ~356K.

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_tutorial.py:240-244`
- Create: `tests/test_heatsink_tutorial_bc.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_heatsink_tutorial_bc.py`:

```python
"""Regression test: bottom segments at y=0 must NOT get convection BC."""

import sys
from pathlib import Path

_examples_dir = str(Path(__file__).resolve().parent.parent / "examples" / "heatflow" / "heatsink")
if _examples_dir not in sys.path:
    sys.path.insert(0, _examples_dir)

from heatsink_tutorial import build_outline_nodes, build_geometry, build_femm_problem, get_lua_script


def test_bottom_segments_not_convection():
    """Segments at y=0 (other than contact) must be insulated (no BC)."""
    nodes = build_outline_nodes()
    geo, lines = build_geometry(nodes)
    problem = build_femm_problem(nodes, geo)
    lua = get_lua_script(problem)

    # Count how many times hi_selectsegment is called at y=0.0
    # Only the contact patch midpoint (y=0) should appear
    select_calls = [line for line in lua.splitlines() if "hi_selectsegment" in line]
    y0_selects = []
    for call in select_calls:
        # Parse: hi_selectsegment(x, y)
        inner = call.split("(")[1].split(")")[0]
        parts = inner.split(",")
        y_val = float(parts[1].strip())
        if abs(y_val) < 1e-6:
            y0_selects.append(call)

    # Only ONE segment at y=0 should be selected: the contact patch
    assert len(y0_selects) == 1, (
        f"Expected 1 segment selection at y=0 (contact only), got {len(y0_selects)}:\n"
        + "\n".join(y0_selects)
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_heatsink_tutorial_bc.py -v`
Expected: FAIL — currently 3 segments are selected at y=0 (contact + 2 bottom segments)

- [ ] **Step 3: Fix the BC assignment loop**

In `examples/heatflow/heatsink/heatsink_tutorial.py`, replace lines 240-244:

```python
    # OLD (buggy): applies convection to bottom segments that should be insulated
    # for i in range(len(nodes)):
    #     if i == 1:
    #         continue
    #     seg = Line(nodes[i], nodes[(i + 1) % len(nodes)])
    #     problem.set_boundary_definition_segment(seg.selection_point(), convection, elementsize=1)

    # NEW: skip bottom segments (y=0) — FEMM treats unassigned segments as insulated
    for i in range(len(nodes)):
        if i == 1:
            continue  # contact patch already assigned
        seg = Line(nodes[i], nodes[(i + 1) % len(nodes)])
        if abs(seg.start_pt.y) < 1e-6 and abs(seg.end_pt.y) < 1e-6:
            continue  # bottom segment — insulated
        problem.set_boundary_definition_segment(seg.selection_point(), convection, elementsize=1)
```

Apply the same fix in `build_parametric()` (line 433-437):

```python
    # In build_parametric(), replace the BC loop:
    for i in range(len(ns)):
        if i == 1:
            continue
        seg = Line(ns[i], ns[(i + 1) % len(ns)])
        if abs(seg.start_pt.y) < 1e-6 and abs(seg.end_pt.y) < 1e-6:
            continue  # bottom segment — insulated
        problem.set_boundary_definition_segment(
            seg.selection_point(), cv, elementsize=1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_heatsink_tutorial_bc.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_heatsink_tutorial_bc.py examples/heatflow/heatsink/heatsink_tutorial.py
git commit -m "fix: skip convection BC on insulated bottom segments

Bottom segments at y=0 flanking the heat source should be insulated
(no BC assigned). Previously they got convection, producing T_avg≈334K
instead of the expected ~356K from the FEMM tutorial."
```

---

### Task 2: Add Bitmap Capture to heatsink_tutorial.py

Add Lua commands for FEMM temperature contour capture and a Python helper to load the resulting BMP.

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_tutorial.py:247-256`

- [ ] **Step 1: Replace get_point_values with raw Lua and add bitmap commands**

The existing `get_point_values()` calls do nothing for heat flow (only magnetic is supported). Replace them with raw Lua `ho_getpointvalues` calls and add bitmap capture.

In `build_femm_problem()`, replace lines 248-256 with:

```python
    # Point values via raw Lua (get_point_values only supports magnetic)
    contact_cx = (CX0 + CX1) / 2
    fin_tip_x = FIN_W / 2
    fin_tip_y = BASE_H + FIN_H

    problem.lua_script.append(f"T_contact = ho_getpointvalues({contact_cx}, 0)")
    problem.lua_script.append(f"T_base = ho_getpointvalues({BASE_W / 2}, {BASE_H / 2})")
    problem.lua_script.append(f"T_fintip = ho_getpointvalues({fin_tip_x}, {fin_tip_y})")

    # Block integral: average temperature
    problem.lua_script.append(f"ho_selectblock({BASE_W / 2}, {BASE_H / 2})")
    problem.lua_script.append("avg_T = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")

    # Bitmap capture: temperature contour plot
    # ho_showdensityplot(legend, gscale, type, upper, lower) — type 0 = temperature
    problem.lua_script.append("ho_showdensityplot(1, 0, 0, T_contact, T_fintip)")
    problem.lua_script.append('ho_savebitmap("heatsink_temperature.bmp")')

    # Write results to CSV
    problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')
    problem.lua_script.append('write(file_out, "T_contact_K = ", T_contact, "\\n")')
    problem.lua_script.append('write(file_out, "T_base_K = ", T_base, "\\n")')
    problem.lua_script.append('write(file_out, "T_fintip_K = ", T_fintip, "\\n")')
```

- [ ] **Step 2: Add load_femm_bitmap helper**

Add after the `plot_results()` function (before section 9):

```python
def load_femm_bitmap(bmp_path: str):
    """Load a BMP file saved by FEMM's ho_savebitmap(), return as numpy array.

    Usage in notebooks:
        img = load_femm_bitmap("path/to/heatsink_temperature.bmp")
        plt.imshow(img)
        plt.axis("off")
        plt.show()
    """
    from PIL import Image
    import numpy as np
    img = Image.open(bmp_path)
    return np.array(img)
```

- [ ] **Step 3: Run existing tests to verify no breakage**

Run: `python -m pytest tests/test_heatsink_tutorial_bc.py -v`
Expected: PASS (the test from Task 1 still passes — same number of y=0 selections)

- [ ] **Step 4: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_tutorial.py
git commit -m "feat: add FEMM bitmap capture and raw Lua point values

Replace no-op get_point_values() calls with raw ho_getpointvalues Lua.
Add ho_showdensityplot + ho_savebitmap for temperature contour capture.
Add load_femm_bitmap() helper for loading BMP in notebooks."
```

---

### Task 3: Remove Parametric Sweep from heatsink_tutorial.py

The parametric sweep (section 9) is superseded by the new `heatsink_parametric.py` module.

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_tutorial.py:389-592`

- [ ] **Step 1: Delete section 9 functions**

Remove these functions from `heatsink_tutorial.py`:
- `build_parametric()` (lines 393-445)
- `run_parametric()` (lines 448-467)
- `plot_parametric()` (lines 473-503)

Also remove the section 9 comment block (lines 389-392).

- [ ] **Step 2: Remove --no-parametric flag and parametric call from main()**

In `main()`, remove:
- Line 519: `parser.add_argument("--no-parametric", ...)`
- Lines 584-586: `if not args.no_parametric: run_parametric(...)`

Update the docstring at the top of the file to remove references to step 9 and `--no-parametric`.

- [ ] **Step 3: Run tests to verify no breakage**

Run: `python -m pytest tests/test_heatsink_tutorial_bc.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_tutorial.py
git commit -m "refactor: remove parametric sweep from heatsink_tutorial

Section 9 (build_parametric, run_parametric, plot_parametric) and the
--no-parametric CLI flag are removed. Superseded by heatsink_parametric.py."
```

---

### Task 4: Create HeatsinkConfig Dataclass + Validation + Sweep Grid

The core data model for the square-wave parametrization.

**Files:**
- Create: `examples/heatflow/heatsink/heatsink_parametric.py`
- Create: `tests/test_heatsink_parametric.py`

- [ ] **Step 1: Write failing tests for HeatsinkConfig**

Create `tests/test_heatsink_parametric.py`:

```python
"""Tests for heatsink_parametric — no FEMM server needed."""

import sys
from pathlib import Path

_examples_dir = str(Path(__file__).resolve().parent.parent / "examples" / "heatflow" / "heatsink")
if _examples_dir not in sys.path:
    sys.path.insert(0, _examples_dir)

from heatsink_parametric import HeatsinkConfig, is_valid, build_sweep_grid


class TestHeatsinkConfig:
    def test_derived_quantities_basic(self):
        """L=20mm, pitch=10mm → n=2, p_actual=10, w_f=D*10, etc."""
        cfg = HeatsinkConfig(base_width=20.0, pitch=10.0, duty_cycle=0.5, base_ratio=0.25)
        assert cfg.n_fins == 2
        assert cfg.pitch_actual == 10.0
        assert cfg.fin_width == 5.0  # 0.5 * 10
        assert cfg.gap == 5.0  # (1-0.5) * 10
        assert cfg.base_height == 6.25  # 0.25 * 25
        assert cfg.fin_height == 18.75  # (1-0.25) * 25

    def test_n_fins_minimum_two(self):
        """n_fins is always >= 2 even with large pitch."""
        cfg = HeatsinkConfig(base_width=4.0, pitch=100.0, duty_cycle=0.5, base_ratio=0.5)
        assert cfg.n_fins == 2

    def test_pitch_actual_fills_width(self):
        """Actual pitch adjusts so n*p_actual == L exactly."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=15.0, duty_cycle=0.25, base_ratio=0.25)
        # round(40/15) = 3 fins → p_actual = 40/3 ≈ 13.333
        assert cfg.n_fins == 3
        assert abs(cfg.n_fins * cfg.pitch_actual - 40.0) < 1e-10


class TestIsValid:
    def test_valid_config(self):
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        # n=4, p=10, w_f=2.5, g=7.5 → all valid
        assert is_valid(cfg)

    def test_fin_too_narrow(self):
        """w_f < 2mm → invalid."""
        cfg = HeatsinkConfig(base_width=20.0, pitch=10.0, duty_cycle=0.1, base_ratio=0.25)
        # w_f = 0.1 * 10 = 1.0 < 2
        assert not is_valid(cfg)

    def test_gap_too_narrow(self):
        """gap < 2mm → invalid."""
        cfg = HeatsinkConfig(base_width=20.0, pitch=5.0, duty_cycle=0.5, base_ratio=0.25)
        # n=4, p_actual=5, w_f=2.5, g=2.5 → valid
        # Try higher duty:
        cfg2 = HeatsinkConfig(base_width=20.0, pitch=5.0, duty_cycle=0.8, base_ratio=0.25)
        # w_f=4.0, g=1.0 < 2 → invalid
        assert not is_valid(cfg2)

    def test_only_one_fin(self):
        """n_fins < 2 would be invalid, but __post_init__ clamps to 2."""
        # With max(2, round(L/p)), n is always >= 2
        cfg = HeatsinkConfig(base_width=4.0, pitch=100.0, duty_cycle=0.5, base_ratio=0.5)
        assert cfg.n_fins == 2  # clamped


class TestBuildSweepGrid:
    def test_all_configs_are_valid(self):
        configs = build_sweep_grid()
        for cfg in configs:
            assert is_valid(cfg), f"Invalid config in grid: {cfg}"

    def test_grid_count_reasonable(self):
        """Spec estimates 150-200 valid configs from 360 total."""
        configs = build_sweep_grid()
        assert 100 <= len(configs) <= 300, f"Got {len(configs)} valid configs"

    def test_all_L_values_present(self):
        """All 10 L values should have at least some valid configs."""
        configs = build_sweep_grid()
        L_values = {cfg.base_width for cfg in configs}
        # Small L values (4, 8) may have 0 valid configs, that's OK
        assert len(L_values) >= 6, f"Only {len(L_values)} distinct L values"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_heatsink_parametric.py -v`
Expected: FAIL — `heatsink_parametric` module does not exist

- [ ] **Step 3: Implement HeatsinkConfig, is_valid, build_sweep_grid**

Create `examples/heatflow/heatsink/heatsink_parametric.py`:

```python
"""Heatsink Parametric Study — Square-Wave Fin Parametrization.

Provides HeatsinkConfig dataclass, sweep grid generation, FEMM problem
builder, sweep engine, and visualization for a full factorial study of
heatsink fin geometry.

Usage:
    python examples/heatflow/heatsink/heatsink_parametric.py
    python examples/heatflow/heatsink/heatsink_parametric.py --start-server
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np
import pandas as pd

from py2femm.client import FemmClient
from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Node, Line
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial


# ---------------------------------------------------------------------------
# Thermal constants (shared with heatsink_tutorial.py)
# ---------------------------------------------------------------------------
P = 10.0            # total power [W]
H_CONV = 10.0       # convection coefficient [W/(m²·K)]
T_AMB = 298.0        # ambient temperature [K]
DEPTH = 100.0        # extrusion depth [mm]
HEIGHT_TOTAL = 25.0  # total height (base + fin) [mm]
CONTACT_WIDTH = 4.0  # heat source width [mm]
SOURCE_WIDTH = 4.0   # source width for L grid [mm]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class HeatsinkConfig:
    """Square-wave parametrization of a heatsink cross-section.

    Primary parameters:
        base_width:    L — total heatsink width [mm]
        pitch:         p — target fin repetition distance [mm]
        duty_cycle:    D — fraction of pitch occupied by fin [0–1]
        base_ratio:    r_b — base height as fraction of total height [0–1]
        height_total:  H_tot — total height = base + fin [mm]
        contact_width: width of heat source patch [mm]
        contact_mode:  "centered", "single_fin", or "between_fins"
    """
    base_width: float
    pitch: float
    duty_cycle: float
    base_ratio: float
    height_total: float = HEIGHT_TOTAL
    contact_width: float = CONTACT_WIDTH
    contact_mode: str = "centered"

    # Derived (computed in __post_init__)
    n_fins: int = field(init=False)
    pitch_actual: float = field(init=False)
    fin_width: float = field(init=False)
    gap: float = field(init=False)
    base_height: float = field(init=False)
    fin_height: float = field(init=False)

    def __post_init__(self):
        self.n_fins = max(2, round(self.base_width / self.pitch))
        self.pitch_actual = self.base_width / self.n_fins
        self.fin_width = self.duty_cycle * self.pitch_actual
        self.gap = (1 - self.duty_cycle) * self.pitch_actual
        self.base_height = self.base_ratio * self.height_total
        self.fin_height = (1 - self.base_ratio) * self.height_total

    @property
    def cross_section_area(self) -> float:
        """A_cross = L × H_b + n × w_f × H_f [mm²]."""
        return self.base_width * self.base_height + self.n_fins * self.fin_width * self.fin_height


def is_valid(cfg: HeatsinkConfig) -> bool:
    """Check manufacturability: fin_width >= 2mm, gap >= 2mm, n_fins >= 2."""
    return cfg.fin_width >= 2.0 and cfg.gap >= 2.0 and cfg.n_fins >= 2


# ---------------------------------------------------------------------------
# Sweep grid
# ---------------------------------------------------------------------------

# Parameter grid values
L_VALUES = [i * SOURCE_WIDTH for i in range(1, 11)]  # 4, 8, ..., 40 mm
PITCH_RATIOS = [0.25, 0.50, 0.75]
DUTY_CYCLES = [0.1, 0.25, 0.5]
BASE_RATIOS = [0.1, 0.25, 0.5, 0.75]


def build_sweep_grid() -> list[HeatsinkConfig]:
    """Generate all valid configs from the full parameter grid.

    Full factorial: 10 × 3 × 3 × 4 = 360 combinations.
    After filtering: ~150-200 valid configs.
    """
    configs = []
    for L, pr, D, rb in product(L_VALUES, PITCH_RATIOS, DUTY_CYCLES, BASE_RATIOS):
        pitch = pr * L
        cfg = HeatsinkConfig(base_width=L, pitch=pitch, duty_cycle=D, base_ratio=rb)
        if is_valid(cfg):
            configs.append(cfg)
    return configs
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_heatsink_parametric.py -v`
Expected: PASS (all TestHeatsinkConfig, TestIsValid, TestBuildSweepGrid tests)

- [ ] **Step 5: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_parametric.py tests/test_heatsink_parametric.py
git commit -m "feat: add HeatsinkConfig dataclass and sweep grid generation

Square-wave parametrization with base_width, pitch, duty_cycle, and
base_ratio. Derived quantities computed in __post_init__. Validity
filter ensures fin_width >= 2mm and gap >= 2mm."
```

---

### Task 5: Add build_femm_problem to heatsink_parametric.py

Builds FEMM geometry + Lua script from a HeatsinkConfig. Returns the complete Lua string ready for client.run().

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_parametric.py`
- Modify: `tests/test_heatsink_parametric.py`

- [ ] **Step 1: Write failing test for Lua output**

Add to `tests/test_heatsink_parametric.py`:

```python
from heatsink_parametric import HeatsinkConfig, is_valid, build_sweep_grid, build_femm_problem


class TestBuildFemmProblem:
    def test_produces_valid_lua(self):
        """Lua script has required commands and no table indexing."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        lua = build_femm_problem(cfg)

        # Must be heat flow problem
        assert "hi_probdef" in lua
        assert '"millimeters"' in lua
        assert '"planar"' in lua

        # Must have geometry
        assert "hi_addnode" in lua
        assert "hi_addsegment" in lua

        # Must have material
        assert "Aluminum" in lua

        # Must extract T_avg, T_max, T_min
        assert "ho_blockintegral(0)" in lua
        assert "ho_getpointvalues" in lua
        assert "AverageTemperature_K" in lua
        assert "T_max_K" in lua
        assert "T_min_K" in lua

        # Must end with quit()
        assert lua.strip().splitlines()[-1].strip() == "quit()"

        # No table indexing (FEMM Lua 4.0)
        assert "[1]" not in lua

    def test_contact_patch_centered(self):
        """Contact patch nodes should be centered on base bottom."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        lua = build_femm_problem(cfg)

        # Contact patch: centered at L/2, width=4mm → cx0=18, cx1=22
        assert "hi_addnode(18.0, 0)" in lua
        assert "hi_addnode(22.0, 0)" in lua

    def test_bottom_segments_insulated(self):
        """No convection BC on bottom segments (y=0, non-contact)."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        lua = build_femm_problem(cfg)

        select_calls = [l for l in lua.splitlines() if "hi_selectsegment" in l]
        y0_selects = []
        for call in select_calls:
            inner = call.split("(")[1].split(")")[0]
            parts = inner.split(",")
            y_val = float(parts[1].strip())
            if abs(y_val) < 1e-6:
                y0_selects.append(call)

        # Only the contact patch midpoint should be selected at y=0
        assert len(y0_selects) == 1, f"Expected 1, got {len(y0_selects)}: {y0_selects}"

    def test_correct_number_of_fins(self):
        """Geometry should have correct fin nodes."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=20.0, duty_cycle=0.5, base_ratio=0.25)
        # n=2, p=20, w_f=10, g=10
        lua = build_femm_problem(cfg)

        # Fin top nodes at y = base_height + fin_height = 6.25 + 18.75 = 25
        fin_top_nodes = [l for l in lua.splitlines()
                         if "hi_addnode" in l and ", 25.0)" in l]
        # 2 fins × 2 top corners = 4 nodes at y=25
        assert len(fin_top_nodes) == 4, f"Expected 4 fin top nodes, got {len(fin_top_nodes)}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_heatsink_parametric.py::TestBuildFemmProblem -v`
Expected: FAIL — `build_femm_problem` not defined

- [ ] **Step 3: Implement build_femm_problem**

Add to `examples/heatflow/heatsink/heatsink_parametric.py`:

```python
# ---------------------------------------------------------------------------
# Geometry + FEMM problem builder
# ---------------------------------------------------------------------------

def _contact_position(cfg: HeatsinkConfig) -> tuple[float, float]:
    """Return (cx0, cx1) for the contact patch based on contact_mode."""
    if cfg.contact_mode == "centered":
        cx0 = (cfg.base_width - cfg.contact_width) / 2
    elif cfg.contact_mode == "single_fin":
        centers = [(i + 0.5) * cfg.pitch_actual for i in range(cfg.n_fins)]
        nearest = min(centers, key=lambda c: abs(c - cfg.base_width / 2))
        cx0 = nearest - cfg.contact_width / 2
    elif cfg.contact_mode == "between_fins":
        centers = sorted(
            [(i + 0.5) * cfg.pitch_actual for i in range(cfg.n_fins)],
            key=lambda c: abs(c - cfg.base_width / 2),
        )
        mid = (centers[0] + centers[1]) / 2
        cx0 = mid - cfg.contact_width / 2
    else:
        raise ValueError(f"Unknown contact_mode: {cfg.contact_mode!r}")
    cx1 = cx0 + cfg.contact_width
    cx0 = max(0.0, cx0)
    cx1 = min(cfg.base_width, cx1)
    return cx0, cx1


def _build_outline_nodes(cfg: HeatsinkConfig) -> list[Node]:
    """Build closed polygon nodes for the heatsink cross-section."""
    cx0, cx1 = _contact_position(cfg)
    H_b = cfg.base_height
    H_f = cfg.fin_height
    L = cfg.base_width

    # Bottom edge + right wall up to base height
    nodes = [
        Node(0, 0),
        Node(cx0, 0),
        Node(cx1, 0),
        Node(L, 0),
        Node(L, H_b),
    ]

    # Fin zigzag: right to left
    for i in range(cfg.n_fins - 1, -1, -1):
        center_x = (i + 0.5) * cfg.pitch_actual
        left_x = center_x - cfg.fin_width / 2
        right_x = center_x + cfg.fin_width / 2
        nodes.extend([
            Node(right_x, H_b),
            Node(right_x, H_b + H_f),
            Node(left_x, H_b + H_f),
            Node(left_x, H_b),
        ])

    # Left wall back to origin
    nodes.append(Node(0, H_b))

    # Deduplicate consecutive nodes
    deduped = [nodes[0]]
    for n in nodes[1:]:
        if abs(n.x - deduped[-1].x) > 1e-6 or abs(n.y - deduped[-1].y) > 1e-6:
            deduped.append(n)
    if (abs(deduped[-1].x - deduped[0].x) < 1e-6
            and abs(deduped[-1].y - deduped[0].y) < 1e-6):
        deduped.pop()

    return deduped


def build_femm_problem(cfg: HeatsinkConfig) -> str:
    """Build complete FEMM heat flow problem from config, return Lua script."""
    nodes = _build_outline_nodes(cfg)
    cx0, cx1 = _contact_position(cfg)

    # Geometry
    geo = Geometry()
    geo.nodes = list(nodes)
    geo.lines = [Line(nodes[i], nodes[(i + 1) % len(nodes)]) for i in range(len(nodes))]

    # FEMM problem
    qs = P / (cfg.contact_width * DEPTH * 1e-6)  # heat flux [W/m²]

    problem = FemmProblem(out_file="heatsink_data.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS, type="planar",
        precision=1e-8, depth=DEPTH, minangle=30,
    )
    problem.create_geometry(geo)

    # Material
    aluminum = HeatFlowMaterial(material_name="Aluminum", kx=200.0, ky=200.0, qv=0.0, kt=0.0)
    problem.add_material(aluminum)
    problem.define_block_label(Node(cfg.base_width / 2, cfg.base_height / 2), aluminum)

    # Boundary conditions
    heat_source = HeatFlowHeatFlux(name="HeatSource", qs=-qs)
    heat_source.Tset = 0; heat_source.Tinf = 0; heat_source.h = 0; heat_source.beta = 0
    problem.add_boundary(heat_source)

    convection = HeatFlowConvection(name="AirConvection", Tinf=T_AMB, h=H_CONV)
    convection.Tset = 0; convection.qs = 0; convection.beta = 0
    problem.add_boundary(convection)

    # Assign BCs — find the contact segment by midpoint
    contact_mid_x = (cx0 + cx1) / 2
    for i in range(len(nodes)):
        seg = Line(nodes[i], nodes[(i + 1) % len(nodes)])
        mid = seg.selection_point()
        if abs(mid.y) < 1e-6 and abs(mid.x - contact_mid_x) < 1e-3:
            problem.set_boundary_definition_segment(mid, heat_source, elementsize=1)
        elif abs(seg.start_pt.y) < 1e-6 and abs(seg.end_pt.y) < 1e-6:
            pass  # bottom segment — insulated
        else:
            problem.set_boundary_definition_segment(mid, convection, elementsize=1)

    # Analysis
    problem.make_analysis("planar")

    # Post-processing: extract metrics
    contact_center_x = (cx0 + cx1) / 2
    outermost_fin_tip_x = 0.5 * cfg.pitch_actual  # leftmost fin center

    problem.lua_script.append(f"T_max = ho_getpointvalues({contact_center_x}, 0)")
    problem.lua_script.append(
        f"T_min = ho_getpointvalues({outermost_fin_tip_x}, "
        f"{cfg.base_height + cfg.fin_height})"
    )

    problem.lua_script.append(f"ho_selectblock({cfg.base_width / 2}, {cfg.base_height / 2})")
    problem.lua_script.append("avg_T = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")

    problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')
    problem.lua_script.append('write(file_out, "T_max_K = ", T_max, "\\n")')
    problem.lua_script.append('write(file_out, "T_min_K = ", T_min, "\\n")')

    problem.close()
    return "\n".join(problem.lua_script)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_heatsink_parametric.py -v`
Expected: PASS (all tests including TestBuildFemmProblem)

- [ ] **Step 5: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_parametric.py tests/test_heatsink_parametric.py
git commit -m "feat: add build_femm_problem for parametric heatsink configs

Builds geometry from HeatsinkConfig using square-wave fin placement.
Contact patch supports centered/single_fin/between_fins modes.
Bottom segments left insulated, extracts T_avg, T_max, T_min."
```

---

### Task 6: Add run_sweep Engine and Result Parsing

The sweep engine runs all configs through FEMM and collects results into a DataFrame.

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_parametric.py`

- [ ] **Step 1: Add parse_results and run_sweep**

Add to `heatsink_parametric.py` after `build_femm_problem`:

```python
# ---------------------------------------------------------------------------
# Result parsing (shared pattern with heatsink_tutorial.py)
# ---------------------------------------------------------------------------

def parse_results(raw_csv: str) -> dict:
    """Parse key=value pairs from CSV output."""
    results = {}
    for line in raw_csv.strip().splitlines():
        line = line.strip()
        if not line or "=" not in line or line.startswith("x,"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().rstrip(",")
        try:
            results[key] = float(val)
        except ValueError:
            results[key] = val
    return results


# ---------------------------------------------------------------------------
# Sweep engine
# ---------------------------------------------------------------------------

def run_sweep(configs: list[HeatsinkConfig], client: FemmClient,
              timeout: int = 120) -> pd.DataFrame:
    """Run all configs via FEMM, return DataFrame with params + metrics.

    Each row contains the config parameters and extracted FEMM results:
    base_width, pitch_ratio, duty_cycle, base_ratio, n_fins, fin_width, gap,
    base_height, fin_height, T_avg, T_max, T_min, R_th, A_cross, R_th_per_area.
    """
    rows = []
    total = len(configs)

    for idx, cfg in enumerate(configs):
        pr = cfg.pitch_actual / cfg.base_width  # pitch ratio for display
        print(
            f"[{idx + 1}/{total}] L={cfg.base_width:.0f}mm, "
            f"pitch/L={pr:.2f}, D={cfg.duty_cycle:.2f}, "
            f"r_b={cfg.base_ratio:.2f}",
            end=" ",
        )

        lua = build_femm_problem(cfg)
        result = client.run(lua, timeout=timeout)

        if result.error or not result.csv_data:
            print(f"FAILED: {result.error}")
            continue

        parsed = parse_results(result.csv_data)
        T_avg = parsed.get("AverageTemperature_K")
        T_max = parsed.get("T_max_K")
        T_min = parsed.get("T_min_K")

        if T_avg is None:
            print("FAILED: no T_avg in output")
            continue

        R_th = (T_avg - T_AMB) / P
        A_cross = cfg.cross_section_area

        row = {
            "base_width": cfg.base_width,
            "pitch_ratio": pr,
            "duty_cycle": cfg.duty_cycle,
            "base_ratio": cfg.base_ratio,
            "n_fins": cfg.n_fins,
            "fin_width": cfg.fin_width,
            "gap": cfg.gap,
            "base_height": cfg.base_height,
            "fin_height": cfg.fin_height,
            "T_avg": T_avg,
            "T_max": T_max,
            "T_min": T_min,
            "R_th": R_th,
            "A_cross": A_cross,
            "R_th_per_area": R_th / A_cross if A_cross > 0 else float("inf"),
        }
        rows.append(row)
        print(f"→ R_th={R_th:.2f} K/W")

    return pd.DataFrame(rows)
```

- [ ] **Step 2: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_parametric.py
git commit -m "feat: add run_sweep engine for parametric heatsink study

Runs all HeatsinkConfig instances through FEMM, parses T_avg/T_max/T_min,
computes R_th and cross-section area. Returns results as a DataFrame."
```

---

### Task 7: Add Plotting Functions

Visualization for the parametric study: 1D sensitivity, 2D heatmaps, scaling, contact comparison, and geometry overlay.

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_parametric.py`

- [ ] **Step 1: Add all plotting functions**

Add to `heatsink_parametric.py`:

```python
# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

# Nominal values for 1D sensitivity plots
NOMINAL = {"base_width": 20.0, "pitch_ratio": 0.50, "duty_cycle": 0.25, "base_ratio": 0.25}


def plot_sensitivity(df: pd.DataFrame, param_name: str, ax=None):
    """1D line plot: R_th and A_cross vs one param, others at nominal.

    Parameters
    ----------
    df : sweep results DataFrame
    param_name : one of "base_width", "pitch_ratio", "duty_cycle", "base_ratio"
    ax : matplotlib Axes (optional, creates new figure if None)
    """
    import matplotlib.pyplot as plt

    # Filter to rows where all other params are at nominal
    mask = pd.Series(True, index=df.index)
    for k, v in NOMINAL.items():
        if k == param_name:
            continue
        mask &= (df[k] - v).abs() < 1e-6
    sub = df[mask].sort_values(param_name)

    if sub.empty:
        return

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))

    color_rth = "tab:red"
    color_area = "tab:blue"

    ax.plot(sub[param_name], sub["R_th"], "o-", color=color_rth, label="R_th")
    ax.set_xlabel(param_name)
    ax.set_ylabel("R_th [K/W]", color=color_rth)
    ax.tick_params(axis="y", labelcolor=color_rth)

    ax2 = ax.twinx()
    ax2.plot(sub[param_name], sub["A_cross"], "s--", color=color_area, label="A_cross")
    ax2.set_ylabel("A_cross [mm²]", color=color_area)
    ax2.tick_params(axis="y", labelcolor=color_area)

    ax.set_title(f"Sensitivity: {param_name}")
    ax.grid(True, alpha=0.3)


def plot_heatmap(df: pd.DataFrame, x_param: str = "pitch_ratio",
                 y_param: str = "duty_cycle", L_values: list[float] | None = None,
                 rb_values: list[float] | None = None):
    """2D heatmap: R_th over (x_param vs y_param).

    Rows = base_ratio values, Cols = representative L values.
    Grey cells indicate invalid/missing combinations.
    """
    import matplotlib.pyplot as plt

    if L_values is None:
        L_values = [12.0, 20.0, 32.0, 40.0]
    if rb_values is None:
        rb_values = sorted(df["base_ratio"].unique())

    fig, axes = plt.subplots(
        len(rb_values), len(L_values),
        figsize=(4 * len(L_values), 3 * len(rb_values)),
        squeeze=False,
    )

    vmin = df["R_th"].min()
    vmax = df["R_th"].max()

    for row, rb in enumerate(rb_values):
        for col, L in enumerate(L_values):
            ax = axes[row, col]
            sub = df[(df["base_ratio"] - rb).abs() < 1e-6
                     & (df["base_width"] - L).abs() < 1e-6]

            if sub.empty:
                ax.set_facecolor("lightgrey")
                ax.text(0.5, 0.5, "No valid\nconfigs", ha="center", va="center",
                        transform=ax.transAxes, fontsize=9, color="grey")
            else:
                pivot = sub.pivot_table(
                    values="R_th", index=y_param, columns=x_param, aggfunc="mean",
                )
                im = ax.imshow(
                    pivot.values, aspect="auto", cmap="viridis_r",
                    vmin=vmin, vmax=vmax, origin="lower",
                )
                ax.set_xticks(range(len(pivot.columns)))
                ax.set_xticklabels([f"{v:.2f}" for v in pivot.columns], fontsize=7)
                ax.set_yticks(range(len(pivot.index)))
                ax.set_yticklabels([f"{v:.2f}" for v in pivot.index], fontsize=7)

            if row == len(rb_values) - 1:
                ax.set_xlabel(x_param)
            if col == 0:
                ax.set_ylabel(y_param)
            ax.set_title(f"L={L:.0f}, r_b={rb:.2f}", fontsize=9)

    fig.suptitle("R_th Heatmaps (pitch/L vs D)", fontsize=13)
    fig.colorbar(im, ax=axes, label="R_th [K/W]", shrink=0.6)
    plt.tight_layout()
    return fig


def plot_scaling(df: pd.DataFrame):
    """R_th and A_cross vs L at best config per L."""
    import matplotlib.pyplot as plt

    best_per_L = df.loc[df.groupby("base_width")["R_th"].idxmin()]
    best_per_L = best_per_L.sort_values("base_width")

    fig, ax1 = plt.subplots(figsize=(8, 5))

    ax1.plot(best_per_L["base_width"], best_per_L["R_th"], "ro-", markersize=8, label="R_th")
    ax1.set_xlabel("Base width L [mm]")
    ax1.set_ylabel("R_th [K/W]", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")

    ax2 = ax1.twinx()
    ax2.plot(best_per_L["base_width"], best_per_L["A_cross"], "bs--", markersize=8, label="A_cross")
    ax2.set_ylabel("A_cross [mm²]", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    ax1.set_title("Scaling: Best R_th per Base Width")
    ax1.grid(True, alpha=0.3)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.tight_layout()
    return fig


def plot_contact_comparison(results: dict[str, pd.DataFrame]):
    """Side-by-side bar chart comparing contact alignment modes.

    Parameters
    ----------
    results : dict mapping mode name ("centered", "single_fin", "between_fins")
              to DataFrame with columns including "R_th" and a label column.
    """
    import matplotlib.pyplot as plt

    modes = list(results.keys())
    fig, ax = plt.subplots(figsize=(10, 5))

    # Assume each DataFrame has same configs (matched by index)
    first_df = results[modes[0]]
    n_configs = len(first_df)
    x = np.arange(n_configs)
    width = 0.25

    for i, mode in enumerate(modes):
        df_mode = results[mode]
        ax.bar(x + i * width, df_mode["R_th"].values, width, label=mode)

    ax.set_xlabel("Configuration #")
    ax.set_ylabel("R_th [K/W]")
    ax.set_title("Contact Mode Comparison (top-5 configs)")
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"#{i+1}" for i in range(n_configs)])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_geometry_overlay(configs: list[HeatsinkConfig], labels: list[str] | None = None):
    """Overlay cross-sections of multiple configs with different colors."""
    import matplotlib.pyplot as plt

    colors = plt.cm.tab10.colors
    fig, ax = plt.subplots(figsize=(12, 6))

    for idx, cfg in enumerate(configs):
        nodes = _build_outline_nodes(cfg)
        xs = [n.x for n in nodes] + [nodes[0].x]
        ys = [n.y for n in nodes] + [nodes[0].y]
        color = colors[idx % len(colors)]
        lbl = labels[idx] if labels else f"Config {idx+1}"
        ax.plot(xs, ys, "-", color=color, linewidth=1.5, label=lbl)
        ax.fill(xs, ys, alpha=0.08, color=color)

    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title("Geometry Overlay — Top Configurations")
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig
```

- [ ] **Step 2: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_parametric.py
git commit -m "feat: add parametric plotting functions

Adds plot_sensitivity (1D, twin y-axes), plot_heatmap (2D grid),
plot_scaling (R_th vs L at best config), plot_contact_comparison
(bar chart), and plot_geometry_overlay (cross-section overlays)."
```

---

### Task 8: Create heatsink_baseline.ipynb

Fixed tutorial reproduction notebook with FEMM bitmap capture.

**Files:**
- Create: `examples/heatflow/heatsink/heatsink_baseline.ipynb`

- [ ] **Step 1: Create the notebook**

Create `examples/heatflow/heatsink/heatsink_baseline.ipynb` with 6 cells:

**Cell 0 (code):** Imports and server health check
```python
import sys
from pathlib import Path

repo_root = Path.cwd().resolve()
while repo_root.name and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

example_dir = str(repo_root / "examples" / "heatflow" / "heatsink")
if example_dir not in sys.path:
    sys.path.insert(0, example_dir)

import heatsink_tutorial as ht
import matplotlib
%matplotlib inline

assert ht.server_is_healthy(), "py2femm server not running on localhost:8082"
print("Server OK")
```

**Cell 1 (code):** Dimensions + geometry build + plot
```python
ht.print_dimensions()
nodes = ht.build_outline_nodes()
geo, lines = ht.build_geometry(nodes)
print(f"\n{len(nodes)} nodes, {len(lines)} segments")
ht.plot_geometry(nodes, lines)
```

**Cell 2 (code):** Build FEMM problem + run
```python
problem = ht.build_femm_problem(nodes, geo)
lua_script = ht.get_lua_script(problem)
print(f"Lua: {len(lua_script)} chars, {lua_script.count(chr(10))} lines")

csv_data = ht.run_femm(lua_script)
print(f"\nRaw output:\n{csv_data.strip()}")
```

**Cell 3 (code):** Parse results: T_avg, R_th, point values
```python
results = ht.parse_results(csv_data)
avg_T, R_th = ht.validate_results(results)

print(f"Average temperature:  {avg_T:.1f} K  ({avg_T - 273.15:.1f} °C)")
print(f"Thermal resistance:   {R_th:.2f} K/W")
print(f"Expected:             ~356 K,  R_th ~ 5.8 K/W")

for k, v in results.items():
    if k != "AverageTemperature_K":
        print(f"  {k} = {v:.1f} K" if isinstance(v, float) else f"  {k} = {v}")
```

**Cell 4 (code):** FEMM temperature contour (bitmap)
```python
import matplotlib.pyplot as plt

# The bitmap is saved by FEMM in the job's working directory.
# Adjust this path to your server's workspace location.
WORKSPACE = r"C:\femm_workspace"  # or /mnt/c/femm_workspace for WSL

import glob
bmps = sorted(glob.glob(f"{WORKSPACE}/**/heatsink_temperature.bmp", recursive=True),
              key=lambda p: Path(p).stat().st_mtime, reverse=True)

if bmps:
    img = ht.load_femm_bitmap(bmps[0])
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(img)
    ax.set_title("FEMM Temperature Contour")
    ax.axis("off")
    plt.tight_layout()
    plt.show()
else:
    print(f"No bitmap found in {WORKSPACE}. Check workspace path.")
```

**Cell 5 (code):** Summary bar chart
```python
ht.plot_results(nodes, avg_T, R_th)
```

Add markdown cells before each code cell with section headers:
- Before cell 0: `# Heat Sink Baseline — FEMM Tutorial #7`
- Before cell 1: `## 1. Geometry`
- Before cell 2: `## 2. Run FEMM (5-fin baseline)`
- Before cell 3: `## 3. Results`
- Before cell 4: `## 4. FEMM Temperature Contour`
- Before cell 5: `## 5. Summary`

- [ ] **Step 2: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_baseline.ipynb
git commit -m "feat: add heatsink_baseline notebook with fixed BCs and bitmap

6-cell notebook reproducing FEMM Tutorial #7 with corrected insulated
bottom segments and FEMM temperature contour bitmap capture."
```

---

### Task 9: Create heatsink_parametric.ipynb

Full parametric study notebook with sweep, analysis, and visualization.

**Files:**
- Create: `examples/heatflow/heatsink/heatsink_parametric.ipynb`

- [ ] **Step 1: Create the notebook**

Create `examples/heatflow/heatsink/heatsink_parametric.ipynb` with cells:

**Markdown:** `# Heatsink Parametric Study — Square-Wave Fin Parametrization`

**Cell 0 (code):** Imports and server health check
```python
import sys
from pathlib import Path

repo_root = Path.cwd().resolve()
while repo_root.name and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

example_dir = str(repo_root / "examples" / "heatflow" / "heatsink")
if example_dir not in sys.path:
    sys.path.insert(0, example_dir)

import heatsink_parametric as hp
import heatsink_tutorial as ht
import matplotlib.pyplot as plt
import pandas as pd
%matplotlib inline

from py2femm.client import FemmClient

assert ht.server_is_healthy(), "py2femm server not running on localhost:8082"
print("Server OK")
```

**Markdown:** `## 1. Parameter Grid`

**Cell 1 (code):** Define grid, filter, preview
```python
configs = hp.build_sweep_grid()
print(f"Full factorial: {len(hp.L_VALUES)}×{len(hp.PITCH_RATIOS)}"
      f"×{len(hp.DUTY_CYCLES)}×{len(hp.BASE_RATIOS)} = "
      f"{len(hp.L_VALUES)*len(hp.PITCH_RATIOS)*len(hp.DUTY_CYCLES)*len(hp.BASE_RATIOS)}")
print(f"Valid configs:  {len(configs)}")

# Preview table
preview = pd.DataFrame([
    {"L": c.base_width, "pitch/L": c.pitch_actual/c.base_width,
     "D": c.duty_cycle, "r_b": c.base_ratio,
     "n": c.n_fins, "w_f": c.fin_width, "g": c.gap}
    for c in configs[:10]
])
display(preview)
```

**Markdown:** `## 2. Run Sweep (~10 min)`

**Cell 2 (code):** Run sweep with progress
```python
client = FemmClient(mode="remote", url="http://localhost:8082")
df = hp.run_sweep(configs, client)
print(f"\nCompleted: {len(df)}/{len(configs)} configs")
df.to_csv("heatsink_parametric_results.csv", index=False)
print("Results saved to heatsink_parametric_results.csv")
```

**Markdown:** `## 3. Results Table`

**Cell 3 (code):** Sortable results
```python
display(df.sort_values("R_th").head(20).style.format({
    "R_th": "{:.3f}", "T_avg": "{:.1f}", "T_max": "{:.1f}", "T_min": "{:.1f}",
    "A_cross": "{:.0f}", "R_th_per_area": "{:.6f}",
}))
```

**Markdown:** `## 4. 1D Sensitivity Analysis`

**Cell 4 (code):** 4 subplots, one per parameter
```python
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
for ax, param in zip(axes.flat, ["base_width", "pitch_ratio", "duty_cycle", "base_ratio"]):
    hp.plot_sensitivity(df, param, ax=ax)
plt.suptitle("1D Sensitivity — R_th and A_cross", fontsize=13)
plt.tight_layout()
plt.show()
```

**Markdown:** `## 5. 2D Heatmaps`

**Cell 5 (code):** R_th heatmaps
```python
hp.plot_heatmap(df)
plt.show()
```

**Markdown:** `## 6. Scaling: R_th vs Base Width`

**Cell 6 (code):** Scaling plot
```python
hp.plot_scaling(df)
plt.show()
```

**Markdown:** `## 7. Contact Mode Comparison`

**Cell 7 (code):** Re-run top-5 with all 3 contact modes
```python
# Top 5 configs by R_th
top5_rows = df.nsmallest(5, "R_th")
top5_configs = [
    hp.HeatsinkConfig(
        base_width=row.base_width, pitch=row.pitch_ratio * row.base_width,
        duty_cycle=row.duty_cycle, base_ratio=row.base_ratio,
    )
    for _, row in top5_rows.iterrows()
]

contact_results = {}
for mode in ["centered", "single_fin", "between_fins"]:
    mode_configs = [
        hp.HeatsinkConfig(
            base_width=c.base_width, pitch=c.pitch, duty_cycle=c.duty_cycle,
            base_ratio=c.base_ratio, contact_mode=mode,
        )
        for c in top5_configs
    ]
    print(f"\n--- Contact mode: {mode} ---")
    contact_results[mode] = hp.run_sweep(mode_configs, client)

hp.plot_contact_comparison(contact_results)
plt.show()
```

**Markdown:** `## 8. Best Configurations`

**Cell 8 (code):** Summary table + geometry overlay
```python
# Best 3 configs
best3 = df.nsmallest(3, "R_th")
print("=== Top 3 Configurations ===\n")
for i, (_, row) in enumerate(best3.iterrows()):
    print(f"#{i+1}: L={row.base_width:.0f}mm, pitch/L={row.pitch_ratio:.2f}, "
          f"D={row.duty_cycle:.2f}, r_b={row.base_ratio:.2f}")
    print(f"     n={row.n_fins:.0f} fins, w_f={row.fin_width:.1f}mm, gap={row.gap:.1f}mm")
    print(f"     R_th={row.R_th:.3f} K/W, A_cross={row.A_cross:.0f} mm²")
    print()

# Geometry overlay
top3_configs = [
    hp.HeatsinkConfig(
        base_width=row.base_width, pitch=row.pitch_ratio * row.base_width,
        duty_cycle=row.duty_cycle, base_ratio=row.base_ratio,
    )
    for _, row in best3.iterrows()
]
labels = [
    f"#{i+1}: L={c.base_width:.0f}, R_th={r:.3f}"
    for i, (c, r) in enumerate(zip(top3_configs, best3["R_th"]))
]
hp.plot_geometry_overlay(top3_configs, labels=labels)
plt.show()
```

- [ ] **Step 2: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_parametric.ipynb
git commit -m "feat: add heatsink_parametric notebook for full factorial sweep

9-cell notebook: parameter grid preview, ~10-min FEMM sweep,
sortable results table, 1D sensitivity, 2D heatmaps, scaling plot,
contact mode comparison, and top-3 geometry overlay."
```

---

## Verification Checklist

After all tasks are complete:

- [ ] `python -m pytest tests/test_heatsink_tutorial_bc.py tests/test_heatsink_parametric.py -v` — all tests pass
- [ ] `python -m pytest tests/test_optimizer_lua.py -v` — existing tests still pass
- [ ] The `heatsink_tutorial.py` module is importable without errors
- [ ] The `heatsink_parametric.py` module is importable without errors
- [ ] Both notebooks open without errors in Jupyter (kernel start, cell 0 imports)
- [ ] With FEMM server running: `heatsink_baseline.ipynb` produces T_avg ≈ 356K (not 334K)
- [ ] With FEMM server running: `heatsink_parametric.ipynb` completes the full sweep and generates all plots
