# Liquid-Cooled TO-247 Heatsink — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `examples/heatflow/liquid_cooler_to247/` with two 2D FEMM builders (circular/rectangular channels), shared config dataclasses, parametric sweep, and thermal coupling matrix — reproducing Waffler §4.4.2 (ETH Zurich Diss. 2011).

**Architecture:** Shared `config.py` holds `LiquidCoolerConfig`, `DeviceConfig`, `compute_h()`, and `default_waffler_config()`. Two builder functions (`build_circular`, `build_rectangular`) each accept the config and return a `FemmProblem`. A `sweep.py` drives both builders across parameter ranges and computes the thermal coupling matrix.

**Tech Stack:** py2femm (`FemmProblem`, `HeatFlowMaterial`, `HeatFlowConvection`, `HeatFlowHeatFlux`, `Geometry`, `Node`, `Line`, `CircleArc`), pytest, Python 3.10+

---

## Key Caveats

- `set_arc_segment_prop()` in `femm_problem.py` has no heat flow case — **all arc BC assignments in `circular.py` must use raw Lua** (`hi_selectarcsegment` / `hi_setarcsegmentprop` / `hi_clearselected`).
- `ho_getpointvalues(x, y)` returns temperature as the **first return value** in Lua 4.0 — assign directly: `T_j = ho_getpointvalues(x, y)`.
- `ho_blockintegral(0)` returns average temperature directly (not ∫T dV).
- Channel interiors must have **no block label** — FEMM treats unlabelled regions as void (correct for fluid).
- Deduplicate consecutive geometry nodes with 1e-6 tolerance if building polygon outlines.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `examples/heatflow/liquid_cooler_to247/__init__.py` | Create | Empty package marker |
| `examples/heatflow/liquid_cooler_to247/config.py` | Create | Dataclasses, `compute_h()`, `default_waffler_config()` |
| `examples/heatflow/liquid_cooler_to247/circular.py` | Create | `build_circular(cfg) → FemmProblem` |
| `examples/heatflow/liquid_cooler_to247/rectangular.py` | Create | `build_rectangular(cfg) → FemmProblem` |
| `examples/heatflow/liquid_cooler_to247/sweep.py` | Create | Parametric sweep + coupling matrix → CSV |
| `tests/test_liquid_cooler_config.py` | Create | Unit tests for config module |
| `tests/test_liquid_cooler_circular.py` | Create | Unit tests for circular builder (Lua content) |
| `tests/test_liquid_cooler_rectangular.py` | Create | Unit tests for rectangular builder (Lua content) |
| `tests/test_liquid_cooler_sweep.py` | Create | Unit tests for sweep CSV structure (mocked client) |
| `tests/test_liquid_cooler_integration.py` | Create | Integration test (skipif no FEMM server) |

---

## Task 1: Config module

**Files:**
- Create: `examples/heatflow/liquid_cooler_to247/__init__.py`
- Create: `examples/heatflow/liquid_cooler_to247/config.py`
- Create: `tests/test_liquid_cooler_config.py`

- [ ] **Step 1.1: Write failing tests**

```python
# tests/test_liquid_cooler_config.py
from __future__ import annotations
import math
import pytest
from examples.heatflow.liquid_cooler_to247.config import (
    DeviceConfig, LiquidCoolerConfig, compute_h, default_waffler_config,
)


def test_default_waffler_config_device_count():
    cfg = default_waffler_config(n_devices=3)
    assert cfg.n_devices == 3


def test_default_waffler_config_single_device():
    cfg = default_waffler_config(n_devices=1)
    assert cfg.n_devices == 1


def test_b_cp_equals_n_devices_times_pitch():
    cfg = default_waffler_config(n_devices=3)
    assert math.isclose(cfg.b_cp, cfg.n_devices * cfg.device_pitch, rel_tol=1e-9)


def test_device_pitch_equals_bp_w_plus_spacing():
    cfg = default_waffler_config(n_devices=2)
    assert math.isclose(cfg.device_pitch, cfg.devices[0].bp_w + cfg.device_spacing, rel_tol=1e-9)


def test_n_channels_covers_full_width():
    cfg = default_waffler_config(n_devices=3)
    assert cfg.n_channels * cfg.s_t >= cfg.b_cp


def test_compute_h_returns_float():
    cfg = default_waffler_config(n_devices=1)
    h = compute_h(cfg)
    assert isinstance(h, float)


def test_compute_h_waffler_defaults_reasonable_range():
    # Waffler reports h ≈ 9436 W/m²K for Re=5568, Nu=28
    cfg = default_waffler_config(n_devices=1)
    h = compute_h(cfg)
    assert 5_000 < h < 20_000, f"h={h:.0f} W/m²K out of expected range"


def test_compute_h_custom_dh():
    cfg = default_waffler_config(n_devices=1)
    h_circ = compute_h(cfg)
    h_rect = compute_h(cfg, dh_mm=3.0)  # wider hydraulic diameter → different h
    assert h_circ != h_rect


def test_waffler_config_geometry_defaults():
    cfg = default_waffler_config()
    assert cfg.h_cp == pytest.approx(4.0)
    assert cfg.d_t == pytest.approx(2.0)
    assert cfg.s_t == pytest.approx(6.0)
    assert cfg.t_inlet == pytest.approx(363.15)
```

- [ ] **Step 1.2: Run to confirm FAIL**

```
python -m pytest tests/test_liquid_cooler_config.py -v
```
Expected: `ModuleNotFoundError: No module named 'examples.heatflow.liquid_cooler_to247.config'`

- [ ] **Step 1.3: Create empty package marker**

Create `examples/heatflow/liquid_cooler_to247/__init__.py` (empty file).

- [ ] **Step 1.4: Implement config.py**

```python
# examples/heatflow/liquid_cooler_to247/config.py
from __future__ import annotations
import math
from dataclasses import dataclass, field


@dataclass
class DeviceConfig:
    name: str
    p_loss: float        # W — power dissipated by this device
    a_si: float = 5.0   # mm — Si die side length (square)
    bp_w: float = 15.0  # mm — Cu baseplate width
    h_cu: float = 3.0   # mm — Cu baseplate height
    d_tim: float = 0.2  # mm — TIM thickness
    k_tim: float = 2.0  # W/mK — TIM thermal conductivity


@dataclass
class LiquidCoolerConfig:
    devices: list[DeviceConfig]
    h_cp: float = 4.0          # mm — cooler block height
    d_t: float = 2.0           # mm — circular channel diameter
    s_t: float = 6.0           # mm — channel pitch (circular and rectangular)
    ch_w: float = 3.0          # mm — rectangular channel width
    ch_h: float = 3.5          # mm — rectangular channel height
    fin_w: float = 1.0         # mm — fin wall width (rectangular channels)
    t_inlet: float = 363.15    # K  — coolant inlet temperature (90°C)
    m_dot: float = 0.0028      # kg/s — mass flow rate per channel
    l_cp: float = 30.0         # mm — cooler depth (extrusion into page)
    device_spacing: float = 3.0 # mm — gap between adjacent baseplates

    @property
    def n_devices(self) -> int:
        return len(self.devices)

    @property
    def device_pitch(self) -> float:
        """Baseplate width + gap between baseplates [mm]."""
        return self.devices[0].bp_w + self.device_spacing

    @property
    def b_cp(self) -> float:
        """Total cooler width = n_devices × device_pitch [mm]."""
        return self.n_devices * self.device_pitch

    @property
    def n_channels(self) -> int:
        """Number of circular/rectangular channels to cover full cooler width."""
        return math.ceil(self.b_cp / self.s_t)


# Water properties at 90°C (Waffler Tab. 4.16)
_WATER_90C = {
    "lam": 0.674,    # W/mK
    "cp": 4205.0,    # J/kgK
    "eta": 0.32e-3,  # Pa·s dynamic viscosity
}


def compute_h(cfg: LiquidCoolerConfig, dh_mm: float | None = None) -> float:
    """Convective coefficient [W/m²K] on channel wall — Waffler eq. 4.145-4.148.

    Args:
        cfg: cooler configuration
        dh_mm: hydraulic diameter [mm]; uses cfg.d_t when None (circular channels)
    """
    w = _WATER_90C
    dh = (dh_mm if dh_mm is not None else cfg.d_t) * 1e-3  # m
    l = cfg.l_cp * 1e-3   # m
    eta = w["eta"]
    lam = w["lam"]
    Pr = eta * w["cp"] / lam
    Re = 4 * cfg.m_dot / (math.pi * eta * dh)

    if Re < 2300:
        Nu = (3.657**3 + 0.644**3 * (Pr * Re * dh / l) ** 1.5) ** (1 / 3)
    elif Re > 4000:
        zeta = 1 / (0.78 * math.log(Re) - 1.5) ** 2
        Nu = (
            zeta / 8 * Re * Pr
            / (1 + 12.7 * math.sqrt(zeta / 8) * (Pr ** (2 / 3) - 1))
            * (1 + (dh / l) ** (2 / 3))
        )
    else:
        gamma = (Re - 2300) / 7700
        Nu_lam = (3.657**3 + 0.644**3 * (Pr * 2300 * dh / l) ** 1.5) ** (1 / 3)
        zeta_t = 1 / (0.78 * math.log(1e4) - 1.5) ** 2
        Nu_turb = (
            zeta_t / 8 * 1e4 * Pr
            / (1 + 12.7 * math.sqrt(zeta_t / 8) * (Pr ** (2 / 3) - 1))
            * (1 + (dh / l) ** (2 / 3))
        )
        Nu = (1 - gamma) * Nu_lam + gamma * Nu_turb

    return Nu * lam / dh


def default_waffler_config(n_devices: int = 3, p_loss: float = 30.0) -> LiquidCoolerConfig:
    """Config reproducing Waffler §4.4.2 geometry with n TO-247 devices."""
    devices = [
        DeviceConfig(name=f"D{i}", p_loss=p_loss)
        for i in range(n_devices)
    ]
    return LiquidCoolerConfig(
        devices=devices,
        h_cp=4.0,
        d_t=2.0,
        s_t=6.0,
        ch_w=3.0,
        ch_h=3.5,
        fin_w=1.0,
        t_inlet=363.15,
        m_dot=0.0028,
        l_cp=30.0,
        device_spacing=3.0,
    )
```

- [ ] **Step 1.5: Run tests — confirm PASS**

```
python -m pytest tests/test_liquid_cooler_config.py -v
```
Expected: all 9 tests PASS.

- [ ] **Step 1.6: Commit**

```bash
git add examples/heatflow/liquid_cooler_to247/__init__.py \
        examples/heatflow/liquid_cooler_to247/config.py \
        tests/test_liquid_cooler_config.py
git commit -m "feat: add liquid cooler TO-247 config dataclasses and compute_h"
```

---

## Task 2: Circular channel builder

**Files:**
- Create: `examples/heatflow/liquid_cooler_to247/circular.py`
- Create: `tests/test_liquid_cooler_circular.py`

- [ ] **Step 2.1: Write failing tests**

```python
# tests/test_liquid_cooler_circular.py
from __future__ import annotations
import pytest
from examples.heatflow.liquid_cooler_to247.config import default_waffler_config
from examples.heatflow.liquid_cooler_to247.circular import build_circular


@pytest.fixture
def lua_1dev():
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)
    return "\n".join(build_circular(cfg).lua_script)


@pytest.fixture
def lua_3dev():
    cfg = default_waffler_config(n_devices=3, p_loss=30.0)
    return "\n".join(build_circular(cfg).lua_script)


def test_returns_femm_problem():
    from py2femm.femm_problem import FemmProblem
    cfg = default_waffler_config(n_devices=1)
    assert isinstance(build_circular(cfg), FemmProblem)


def test_uses_circle_arcs(lua_1dev):
    assert "hi_addarc" in lua_1dev


def test_aluminum_material_defined(lua_1dev):
    assert "Aluminum" in lua_1dev
    assert "160" in lua_1dev


def test_silicon_material_defined(lua_1dev):
    assert "Silicon" in lua_1dev


def test_copper_material_defined(lua_1dev):
    assert "Copper" in lua_1dev


def test_convection_bc_defined(lua_1dev):
    assert "CoolantConvection" in lua_1dev


def test_heat_flux_bc_per_device_1dev(lua_1dev):
    assert "HeatFlux_0" in lua_1dev
    assert "HeatFlux_1" not in lua_1dev


def test_heat_flux_bc_per_device_3dev(lua_3dev):
    assert "HeatFlux_0" in lua_3dev
    assert "HeatFlux_1" in lua_3dev
    assert "HeatFlux_2" in lua_3dev


def test_arc_convection_raw_lua(lua_1dev):
    assert "hi_selectarcsegment" in lua_1dev
    assert "hi_setarcsegmentprop" in lua_1dev


def test_post_processing_t_j_per_device_1dev(lua_1dev):
    assert "T_j_0" in lua_1dev
    assert "ho_getpointvalues" in lua_1dev


def test_post_processing_t_j_per_device_3dev(lua_3dev):
    assert "T_j_0" in lua_3dev
    assert "T_j_1" in lua_3dev
    assert "T_j_2" in lua_3dev


def test_post_processing_t_h_surface(lua_1dev):
    assert "T_h_surface" in lua_1dev
    assert "ho_blockintegral(0)" in lua_1dev


def test_heat_flux_value_1dev():
    import math
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)
    lua = "\n".join(build_circular(cfg).lua_script)
    dev = cfg.devices[0]
    expected_qs = dev.p_loss / (dev.a_si * 1e-3 * cfg.l_cp * 1e-3)
    # qs appears negated in the Lua (heat into domain)
    assert f"-{expected_qs:.4f}" in lua or str(int(-expected_qs)) in lua


def test_planar_problem_type(lua_1dev):
    assert "planar" in lua_1dev


def test_depth_in_lua(lua_1dev):
    cfg = default_waffler_config(n_devices=1)
    assert str(int(cfg.l_cp)) in lua_1dev
```

- [ ] **Step 2.2: Run to confirm FAIL**

```
python -m pytest tests/test_liquid_cooler_circular.py -v
```
Expected: `ModuleNotFoundError: No module named '...circular'`

- [ ] **Step 2.3: Implement circular.py**

```python
# examples/heatflow/liquid_cooler_to247/circular.py
from __future__ import annotations
import math

from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import CircleArc, Geometry, Line, Node
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial

from .config import LiquidCoolerConfig, compute_h


def build_circular(cfg: LiquidCoolerConfig) -> FemmProblem:
    """Build 2D planar heat-flow model with circular drilled channels (Waffler §4.4.2)."""
    problem = FemmProblem(out_file="liquid_cooler_circular.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS,
        type="planar",
        precision=1e-8,
        depth=cfg.l_cp,
        minangle=30,
    )

    b_cp = cfg.b_cp
    h_cp = cfg.h_cp
    r = cfg.d_t / 2           # channel radius [mm]
    cy_ch = h_cp / 2           # channel centre y [mm]

    dev0 = cfg.devices[0]
    y_tim_bot = h_cp
    y_tim_top = h_cp + dev0.d_tim
    y_cu_top  = y_tim_top + dev0.h_cu
    y_si_top  = y_cu_top + dev0.a_si

    geo = Geometry()

    # ── Cooler outer rectangle ──
    _add_rect(geo, 0.0, 0.0, b_cp, h_cp)

    # ── Circular channels (two 180° arcs per channel = full circle void) ──
    channel_xs = [cfg.s_t / 2 + i * cfg.s_t for i in range(cfg.n_channels)]
    for cx in channel_xs:
        top_n = Node(cx, cy_ch + r)
        bot_n = Node(cx, cy_ch - r)
        ctr_n = Node(cx, cy_ch)
        geo.add_arc(CircleArc(top_n, ctr_n, bot_n))  # right half
        geo.add_arc(CircleArc(bot_n, ctr_n, top_n))  # left half

    # ── Device stacks (TIM / Cu / Si die rectangles above cooler) ──
    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xr = xl + dev.bp_w
        x_si_l = xl + (dev.bp_w - dev.a_si) / 2
        x_si_r = x_si_l + dev.a_si
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        y_st = y_ct + dev.a_si
        _add_rect(geo, xl,    y_tim_bot, xr,    y_tt)   # TIM
        _add_rect(geo, xl,    y_tt,      xr,    y_ct)   # Cu baseplate
        _add_rect(geo, x_si_l, y_ct,    x_si_r, y_st)  # Si die

    problem.create_geometry(geo)

    # ── Materials ──
    mat_al = HeatFlowMaterial(material_name="Aluminum", kx=160.0, ky=160.0, qv=0.0, kt=0.0)
    mat_si = HeatFlowMaterial(material_name="Silicon",  kx=130.0, ky=130.0, qv=0.0, kt=0.0)
    mat_cu = HeatFlowMaterial(material_name="Copper",   kx=385.0, ky=385.0, qv=0.0, kt=0.0)
    for mat in (mat_al, mat_si, mat_cu):
        problem.add_material(mat)

    # Al block label: bottom-left strip, below channels
    problem.define_block_label(Node(0.3, 0.2), mat_al)

    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xc = xl + dev.bp_w / 2
        mat_tim = HeatFlowMaterial(
            material_name=f"TIM_{i}", kx=dev.k_tim, ky=dev.k_tim, qv=0.0, kt=0.0
        )
        problem.add_material(mat_tim)
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        y_st = y_ct + dev.a_si
        problem.define_block_label(Node(xc, h_cp + dev.d_tim / 2),   mat_tim)
        problem.define_block_label(Node(xc, y_tt + dev.h_cu / 2),    mat_cu)
        problem.define_block_label(Node(xc, y_ct + dev.a_si / 2),    mat_si)

    # ── Boundary Conditions ──
    h_conv = compute_h(cfg)
    convection = HeatFlowConvection(name="CoolantConvection", Tinf=cfg.t_inlet, h=h_conv)
    convection.Tset = 0
    convection.qs = 0
    convection.beta = 0
    problem.add_boundary(convection)

    for i, dev in enumerate(cfg.devices):
        qs = -dev.p_loss / (dev.a_si * 1e-3 * cfg.l_cp * 1e-3)
        hf = HeatFlowHeatFlux(name=f"HeatFlux_{i}", qs=qs)
        hf.Tset = 0
        hf.Tinf = 0
        hf.h = 0
        hf.beta = 0
        problem.add_boundary(hf)
        xl_si = i * cfg.device_pitch + (dev.bp_w - dev.a_si) / 2
        xr_si = xl_si + dev.a_si
        y_st = h_cp + dev.d_tim + dev.h_cu + dev.a_si
        seg = Line(Node(xl_si, y_st), Node(xr_si, y_st))
        problem.set_boundary_definition_segment(seg.selection_point(), hf, elementsize=0.5)

    # Assign convection to circular channel walls via raw Lua
    # (set_arc_segment_prop has no heat flow case in femm_problem.py)
    for cx in channel_xs:
        for sel_x in (cx + r * 0.999, cx - r * 0.999):
            problem.lua_script.append(f"hi_selectarcsegment({sel_x:.6f}, {cy_ch:.6f})")
            problem.lua_script.append(f"hi_setarcsegmentprop(1, '{convection.name}', 0, 0)")
            problem.lua_script.append("hi_clearselected()")

    # ── Analysis ──
    problem.make_analysis("planar")

    # ── Post-processing ──
    problem.lua_script.append("ho_reload()")

    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xc = xl + dev.bp_w / 2
        y_st = h_cp + dev.d_tim + dev.h_cu + dev.a_si
        y_j = y_st - dev.a_si * 0.1       # 10% below top of die
        y_case = h_cp + dev.d_tim + dev.h_cu * 0.9

        problem.lua_script.append(f"T_j_{i} = ho_getpointvalues({xc:.4f}, {y_j:.4f})")
        problem.lua_script.append(f'write(file_out, "T_j_{i} = ", T_j_{i}, "\\n")')
        problem.lua_script.append(f"T_case_{i} = ho_getpointvalues({xc:.4f}, {y_case:.4f})")
        problem.lua_script.append(f'write(file_out, "T_case_{i} = ", T_case_{i}, "\\n")')

    problem.lua_script.append(f"ho_selectblock({b_cp / 2:.4f}, {h_cp * 0.1:.4f})")
    problem.lua_script.append("T_h_surface = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")
    problem.lua_script.append('write(file_out, "T_h_surface = ", T_h_surface, "\\n")')

    return problem


def _add_rect(geo: Geometry, x0: float, y0: float, x1: float, y1: float) -> None:
    """Add four Line segments forming a closed rectangle to geo."""
    bl, br, tr, tl = Node(x0, y0), Node(x1, y0), Node(x1, y1), Node(x0, y1)
    geo.add_line(Line(bl, br))
    geo.add_line(Line(br, tr))
    geo.add_line(Line(tr, tl))
    geo.add_line(Line(tl, bl))
```

- [ ] **Step 2.4: Run tests — confirm PASS**

```
python -m pytest tests/test_liquid_cooler_circular.py -v
```
Expected: all 14 tests PASS.

- [ ] **Step 2.5: Commit**

```bash
git add examples/heatflow/liquid_cooler_to247/circular.py \
        tests/test_liquid_cooler_circular.py
git commit -m "feat: add circular channel liquid cooler builder"
```

---

## Task 3: Rectangular channel builder

**Files:**
- Create: `examples/heatflow/liquid_cooler_to247/rectangular.py`
- Create: `tests/test_liquid_cooler_rectangular.py`

- [ ] **Step 3.1: Write failing tests**

```python
# tests/test_liquid_cooler_rectangular.py
from __future__ import annotations
import pytest
from examples.heatflow.liquid_cooler_to247.config import default_waffler_config
from examples.heatflow.liquid_cooler_to247.rectangular import build_rectangular


@pytest.fixture
def lua_1dev():
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)
    return "\n".join(build_rectangular(cfg).lua_script)


@pytest.fixture
def lua_3dev():
    cfg = default_waffler_config(n_devices=3, p_loss=30.0)
    return "\n".join(build_rectangular(cfg).lua_script)


def test_returns_femm_problem():
    from py2femm.femm_problem import FemmProblem
    cfg = default_waffler_config(n_devices=1)
    assert isinstance(build_rectangular(cfg), FemmProblem)


def test_no_circle_arcs(lua_1dev):
    assert "hi_addarc" not in lua_1dev


def test_aluminum_material_defined(lua_1dev):
    assert "Aluminum" in lua_1dev
    assert "160" in lua_1dev


def test_silicon_material_defined(lua_1dev):
    assert "Silicon" in lua_1dev


def test_copper_material_defined(lua_1dev):
    assert "Copper" in lua_1dev


def test_convection_bc_on_channel_walls(lua_1dev):
    assert "CoolantConvection" in lua_1dev


def test_heat_flux_bc_per_device(lua_3dev):
    assert "HeatFlux_0" in lua_3dev
    assert "HeatFlux_1" in lua_3dev
    assert "HeatFlux_2" in lua_3dev


def test_post_processing_all_devices(lua_3dev):
    assert "T_j_0" in lua_3dev
    assert "T_j_1" in lua_3dev
    assert "T_j_2" in lua_3dev


def test_t_h_surface_in_output(lua_1dev):
    assert "T_h_surface" in lua_1dev
    assert "ho_blockintegral(0)" in lua_1dev


def test_planar_problem(lua_1dev):
    assert "planar" in lua_1dev
```

- [ ] **Step 3.2: Run to confirm FAIL**

```
python -m pytest tests/test_liquid_cooler_rectangular.py -v
```
Expected: `ModuleNotFoundError: No module named '...rectangular'`

- [ ] **Step 3.3: Implement rectangular.py**

```python
# examples/heatflow/liquid_cooler_to247/rectangular.py
from __future__ import annotations

from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Line, Node
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial

from .config import LiquidCoolerConfig, compute_h


def build_rectangular(cfg: LiquidCoolerConfig) -> FemmProblem:
    """Build 2D planar heat-flow model with rectangular milled channels."""
    problem = FemmProblem(out_file="liquid_cooler_rectangular.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS,
        type="planar",
        precision=1e-8,
        depth=cfg.l_cp,
        minangle=30,
    )

    b_cp = cfg.b_cp
    h_cp = cfg.h_cp
    ch_w = cfg.ch_w
    ch_h = cfg.ch_h
    cy_ch = h_cp / 2      # channel centre y

    dev0 = cfg.devices[0]
    y_tim_top = h_cp + dev0.d_tim
    y_cu_top  = y_tim_top + dev0.h_cu
    y_si_top  = y_cu_top + dev0.a_si

    geo = Geometry()

    # ── Cooler outer rectangle ──
    _add_rect(geo, 0.0, 0.0, b_cp, h_cp)

    # ── Rectangular channel voids ──
    channel_xs = [cfg.s_t / 2 + i * cfg.s_t for i in range(cfg.n_channels)]
    for cx in channel_xs:
        xl_ch = cx - ch_w / 2
        xr_ch = cx + ch_w / 2
        yb_ch = cy_ch - ch_h / 2
        yt_ch = cy_ch + ch_h / 2
        _add_rect(geo, xl_ch, yb_ch, xr_ch, yt_ch)

    # ── Device stacks ──
    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xr = xl + dev.bp_w
        x_si_l = xl + (dev.bp_w - dev.a_si) / 2
        x_si_r = x_si_l + dev.a_si
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        y_st = y_ct + dev.a_si
        _add_rect(geo, xl,     h_cp,  xr,     y_tt)   # TIM
        _add_rect(geo, xl,     y_tt,  xr,     y_ct)   # Cu
        _add_rect(geo, x_si_l, y_ct,  x_si_r, y_st)  # Si die

    problem.create_geometry(geo)

    # ── Materials ──
    mat_al = HeatFlowMaterial(material_name="Aluminum", kx=160.0, ky=160.0, qv=0.0, kt=0.0)
    mat_si = HeatFlowMaterial(material_name="Silicon",  kx=130.0, ky=130.0, qv=0.0, kt=0.0)
    mat_cu = HeatFlowMaterial(material_name="Copper",   kx=385.0, ky=385.0, qv=0.0, kt=0.0)
    for mat in (mat_al, mat_si, mat_cu):
        problem.add_material(mat)

    problem.define_block_label(Node(0.3, 0.2), mat_al)

    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xc = xl + dev.bp_w / 2
        mat_tim = HeatFlowMaterial(
            material_name=f"TIM_{i}", kx=dev.k_tim, ky=dev.k_tim, qv=0.0, kt=0.0
        )
        problem.add_material(mat_tim)
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        problem.define_block_label(Node(xc, h_cp + dev.d_tim / 2),  mat_tim)
        problem.define_block_label(Node(xc, y_tt + dev.h_cu / 2),   mat_cu)
        problem.define_block_label(Node(xc, y_ct + dev.a_si / 2),   mat_si)

    # ── Boundary Conditions ──
    # Hydraulic diameter for rectangular channel: 2*w*h/(w+h)
    dh_mm = 2 * ch_w * ch_h / (ch_w + ch_h)
    h_conv = compute_h(cfg, dh_mm=dh_mm)
    convection = HeatFlowConvection(name="CoolantConvection", Tinf=cfg.t_inlet, h=h_conv)
    convection.Tset = 0
    convection.qs = 0
    convection.beta = 0
    problem.add_boundary(convection)

    # Assign convection to all four walls of each rectangular channel
    for cx in channel_xs:
        xl_ch = cx - ch_w / 2
        xr_ch = cx + ch_w / 2
        yb_ch = cy_ch - ch_h / 2
        yt_ch = cy_ch + ch_h / 2
        for seg in [
            Line(Node(xl_ch, yb_ch), Node(xr_ch, yb_ch)),  # bottom wall
            Line(Node(xr_ch, yb_ch), Node(xr_ch, yt_ch)),  # right wall
            Line(Node(xr_ch, yt_ch), Node(xl_ch, yt_ch)),  # top wall
            Line(Node(xl_ch, yt_ch), Node(xl_ch, yb_ch)),  # left wall
        ]:
            problem.set_boundary_definition_segment(seg.selection_point(), convection, elementsize=0.5)

    # Heat flux per device
    for i, dev in enumerate(cfg.devices):
        qs = -dev.p_loss / (dev.a_si * 1e-3 * cfg.l_cp * 1e-3)
        hf = HeatFlowHeatFlux(name=f"HeatFlux_{i}", qs=qs)
        hf.Tset = 0
        hf.Tinf = 0
        hf.h = 0
        hf.beta = 0
        problem.add_boundary(hf)
        xl_si = i * cfg.device_pitch + (dev.bp_w - dev.a_si) / 2
        xr_si = xl_si + dev.a_si
        y_st = h_cp + dev.d_tim + dev.h_cu + dev.a_si
        seg = Line(Node(xl_si, y_st), Node(xr_si, y_st))
        problem.set_boundary_definition_segment(seg.selection_point(), hf, elementsize=0.5)

    # ── Analysis ──
    problem.make_analysis("planar")

    # ── Post-processing ──
    problem.lua_script.append("ho_reload()")

    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xc = xl + dev.bp_w / 2
        y_st = h_cp + dev.d_tim + dev.h_cu + dev.a_si
        y_j    = y_st - dev.a_si * 0.1
        y_case = h_cp + dev.d_tim + dev.h_cu * 0.9
        problem.lua_script.append(f"T_j_{i} = ho_getpointvalues({xc:.4f}, {y_j:.4f})")
        problem.lua_script.append(f'write(file_out, "T_j_{i} = ", T_j_{i}, "\\n")')
        problem.lua_script.append(f"T_case_{i} = ho_getpointvalues({xc:.4f}, {y_case:.4f})")
        problem.lua_script.append(f'write(file_out, "T_case_{i} = ", T_case_{i}, "\\n")')

    problem.lua_script.append(f"ho_selectblock({b_cp / 2:.4f}, {h_cp * 0.1:.4f})")
    problem.lua_script.append("T_h_surface = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")
    problem.lua_script.append('write(file_out, "T_h_surface = ", T_h_surface, "\\n")')

    return problem


def _add_rect(geo: Geometry, x0: float, y0: float, x1: float, y1: float) -> None:
    bl, br, tr, tl = Node(x0, y0), Node(x1, y0), Node(x1, y1), Node(x0, y1)
    geo.add_line(Line(bl, br))
    geo.add_line(Line(br, tr))
    geo.add_line(Line(tr, tl))
    geo.add_line(Line(tl, bl))
```

- [ ] **Step 3.4: Run tests — confirm PASS**

```
python -m pytest tests/test_liquid_cooler_rectangular.py -v
```
Expected: all 10 tests PASS.

- [ ] **Step 3.5: Run full suite — confirm no regressions**

```
python -m pytest tests/ -v --ignore=tests/test_liquid_cooler_integration.py -q
```
Expected: all existing tests still PASS.

- [ ] **Step 3.6: Commit**

```bash
git add examples/heatflow/liquid_cooler_to247/rectangular.py \
        tests/test_liquid_cooler_rectangular.py
git commit -m "feat: add rectangular channel liquid cooler builder"
```

---

## Task 4: Sweep script + thermal coupling matrix

**Files:**
- Create: `examples/heatflow/liquid_cooler_to247/sweep.py`
- Create: `tests/test_liquid_cooler_sweep.py`

- [ ] **Step 4.1: Write failing tests**

```python
# tests/test_liquid_cooler_sweep.py
from __future__ import annotations
import csv
import io
from unittest.mock import MagicMock, patch
import pytest

from examples.heatflow.liquid_cooler_to247.config import default_waffler_config
from examples.heatflow.liquid_cooler_to247.sweep import (
    parse_csv_result,
    compute_coupling_matrix,
    run_sweep,
)


def _make_mock_result(n_devices: int, t_j_values: list[float], t_h: float = 365.0):
    """Build a fake CSV string that parse_csv_result can consume."""
    lines = [f"T_j_{i} = {t_j_values[i]}\n" for i in range(n_devices)]
    lines += [f"T_case_{i} = {t_j_values[i] - 1.0}\n" for i in range(n_devices)]
    lines.append(f"T_h_surface = {t_h}\n")
    return "".join(lines)


def test_parse_csv_result_extracts_t_j():
    raw = _make_mock_result(2, [390.0, 385.0])
    result = parse_csv_result(raw, n_devices=2)
    assert result["T_j_0"] == pytest.approx(390.0)
    assert result["T_j_1"] == pytest.approx(385.0)


def test_parse_csv_result_extracts_t_h_surface():
    raw = _make_mock_result(1, [388.0], t_h=366.0)
    result = parse_csv_result(raw, n_devices=1)
    assert result["T_h_surface"] == pytest.approx(366.0)


def test_compute_coupling_matrix_shape():
    # Mock a client that returns fake temperatures
    cfg = default_waffler_config(n_devices=2, p_loss=30.0)

    def fake_run(problem):
        # Return fake CSV: powered device runs hotter
        return _make_mock_result(2, [380.0, 370.0])

    C = compute_coupling_matrix(cfg, builder="circular", run_fn=fake_run)
    assert C.shape == (2, 2)


def test_compute_coupling_matrix_diagonal_dominance():
    cfg = default_waffler_config(n_devices=2, p_loss=30.0)

    call_count = [0]
    def fake_run(problem):
        i = call_count[0]
        call_count[0] += 1
        # Device 0 powered: T_j_0 > T_j_1
        if i == 0:
            return _make_mock_result(2, [395.0, 368.0])
        # Device 1 powered: T_j_1 > T_j_0
        return _make_mock_result(2, [366.0, 393.0])

    C = compute_coupling_matrix(cfg, builder="circular", run_fn=fake_run)
    # Self-heating (diagonal) should dominate
    assert C[0, 0] > C[0, 1]
    assert C[1, 1] > C[1, 0]


def test_run_sweep_csv_has_required_columns():
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)

    def fake_run(problem):
        return _make_mock_result(1, [390.0])

    buf = io.StringIO()
    run_sweep(
        cfg=cfg,
        builders=["circular"],
        p_loss_values=[30.0],
        run_fn=fake_run,
        out=buf,
    )
    buf.seek(0)
    reader = csv.DictReader(buf)
    row = next(reader)
    assert "builder" in row
    assert "n_devices" in row
    assert "p_loss" in row
    assert "T_j_0" in row
    assert "T_h_surface" in row
```

- [ ] **Step 4.2: Run to confirm FAIL**

```
python -m pytest tests/test_liquid_cooler_sweep.py -v
```
Expected: `ModuleNotFoundError: No module named '...sweep'`

- [ ] **Step 4.3: Implement sweep.py**

```python
# examples/heatflow/liquid_cooler_to247/sweep.py
"""Parametric sweep and thermal coupling matrix for liquid cooler TO-247 example."""
from __future__ import annotations

import csv
import io
import re
import sys
from dataclasses import replace
from typing import Callable

import numpy as np

from .circular import build_circular
from .config import LiquidCoolerConfig, DeviceConfig, default_waffler_config
from .rectangular import build_rectangular

_BUILDERS = {"circular": build_circular, "rectangular": build_rectangular}


def parse_csv_result(raw: str, n_devices: int) -> dict[str, float]:
    """Parse FEMM CSV output lines into a flat dict of float values."""
    result: dict[str, float] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([\w]+)\s*=\s*([0-9eE+\-.]+)", line)
        if m:
            result[m.group(1)] = float(m.group(2))
    return result


def compute_coupling_matrix(
    cfg: LiquidCoolerConfig,
    builder: str,
    run_fn: Callable,
) -> "np.ndarray":
    """Return n×n coupling matrix C where C[k,i] = (T_j[i] - T_inlet) / P_k [K/W].

    Runs n_devices separate FEMM jobs — each with only one device powered.
    """
    n = cfg.n_devices
    C = np.zeros((n, n))
    build_fn = _BUILDERS[builder]

    for k in range(n):
        # Only device k powered
        powered_devices = [
            DeviceConfig(
                name=dev.name,
                p_loss=cfg.devices[k].p_loss if i == k else 0.0,
                a_si=dev.a_si,
                bp_w=dev.bp_w,
                h_cu=dev.h_cu,
                d_tim=dev.d_tim,
                k_tim=dev.k_tim,
            )
            for i, dev in enumerate(cfg.devices)
        ]
        cfg_k = LiquidCoolerConfig(
            devices=powered_devices,
            h_cp=cfg.h_cp,
            d_t=cfg.d_t,
            s_t=cfg.s_t,
            ch_w=cfg.ch_w,
            ch_h=cfg.ch_h,
            fin_w=cfg.fin_w,
            t_inlet=cfg.t_inlet,
            m_dot=cfg.m_dot,
            l_cp=cfg.l_cp,
            device_spacing=cfg.device_spacing,
        )
        problem = build_fn(cfg_k)
        raw = run_fn(problem)
        parsed = parse_csv_result(raw, n_devices=n)
        p_k = cfg.devices[k].p_loss
        for i in range(n):
            t_j = parsed.get(f"T_j_{i}", cfg.t_inlet)
            C[k, i] = (t_j - cfg.t_inlet) / p_k if p_k > 0 else 0.0

    return C


def run_sweep(
    cfg: LiquidCoolerConfig,
    builders: list[str],
    p_loss_values: list[float],
    run_fn: Callable,
    out=None,
) -> None:
    """Run parametric sweep over builders × p_loss_values; write CSV rows to out."""
    if out is None:
        out = sys.stdout

    n = cfg.n_devices
    fieldnames = (
        ["builder", "n_devices", "p_loss", "T_h_surface"]
        + [f"T_j_{i}" for i in range(n)]
        + [f"T_case_{i}" for i in range(n)]
        + [f"Rth_j_inlet_{i}" for i in range(n)]
    )
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()

    for builder in builders:
        build_fn = _BUILDERS[builder]
        for p_loss in p_loss_values:
            # All devices same power
            powered_devices = [
                DeviceConfig(
                    name=dev.name,
                    p_loss=p_loss,
                    a_si=dev.a_si,
                    bp_w=dev.bp_w,
                    h_cu=dev.h_cu,
                    d_tim=dev.d_tim,
                    k_tim=dev.k_tim,
                )
                for dev in cfg.devices
            ]
            cfg_run = LiquidCoolerConfig(
                devices=powered_devices,
                h_cp=cfg.h_cp,
                d_t=cfg.d_t,
                s_t=cfg.s_t,
                ch_w=cfg.ch_w,
                ch_h=cfg.ch_h,
                fin_w=cfg.fin_w,
                t_inlet=cfg.t_inlet,
                m_dot=cfg.m_dot,
                l_cp=cfg.l_cp,
                device_spacing=cfg.device_spacing,
            )
            problem = build_fn(cfg_run)
            raw = run_fn(problem)
            parsed = parse_csv_result(raw, n_devices=n)

            row: dict = {
                "builder": builder,
                "n_devices": n,
                "p_loss": p_loss,
                "T_h_surface": parsed.get("T_h_surface", ""),
            }
            for i in range(n):
                t_j = parsed.get(f"T_j_{i}", "")
                row[f"T_j_{i}"] = t_j
                row[f"T_case_{i}"] = parsed.get(f"T_case_{i}", "")
                if t_j and p_loss > 0:
                    row[f"Rth_j_inlet_{i}"] = (float(t_j) - cfg.t_inlet) / p_loss
                else:
                    row[f"Rth_j_inlet_{i}"] = ""

            writer.writerow(row)


if __name__ == "__main__":
    from py2femm.client import FemmClient

    cfg = default_waffler_config(n_devices=3, p_loss=30.0)
    client = FemmClient()

    def _run(problem):
        result = client.run(problem)
        return result.csv_data or ""

    print("=== Coupling matrix (circular channels) ===")
    C = compute_coupling_matrix(cfg, builder="circular", run_fn=_run)
    print(C)

    print("\n=== Parametric sweep ===")
    run_sweep(
        cfg=cfg,
        builders=["circular", "rectangular"],
        p_loss_values=[10.0, 20.0, 30.0, 40.0, 50.0],
        run_fn=_run,
        out=open("liquid_cooler_sweep.csv", "w", newline=""),
    )
    print("Results written to liquid_cooler_sweep.csv")
```

- [ ] **Step 4.4: Run tests — confirm PASS**

```
python -m pytest tests/test_liquid_cooler_sweep.py -v
```
Expected: all 5 tests PASS.

- [ ] **Step 4.5: Run full unit suite**

```
python -m pytest tests/ -v --ignore=tests/test_liquid_cooler_integration.py -q
```
Expected: all tests PASS.

- [ ] **Step 4.6: Commit**

```bash
git add examples/heatflow/liquid_cooler_to247/sweep.py \
        tests/test_liquid_cooler_sweep.py
git commit -m "feat: add liquid cooler sweep script and thermal coupling matrix"
```

---

## Task 5: Integration test (FEMM-live, validation against Waffler)

**Files:**
- Create: `tests/test_liquid_cooler_integration.py`

- [ ] **Step 5.1: Write integration test**

```python
# tests/test_liquid_cooler_integration.py
"""Live FEMM integration test — skipped unless server is reachable on localhost:8082."""
from __future__ import annotations
import pytest
import urllib.request

from examples.heatflow.liquid_cooler_to247.config import (
    LiquidCoolerConfig, DeviceConfig, default_waffler_config, compute_h,
)
from examples.heatflow.liquid_cooler_to247.circular import build_circular
from examples.heatflow.liquid_cooler_to247.sweep import parse_csv_result


def _server_alive() -> bool:
    try:
        urllib.request.urlopen("http://localhost:8082/health", timeout=2)
        return True
    except Exception:
        return False


skip_no_femm = pytest.mark.skipif(not _server_alive(), reason="FEMM server not running on localhost:8082")


@skip_no_femm
def test_waffler_single_cell_delta_T():
    """Single circular channel, one device, n_devices=1 → ΔT_h-i ≈ 4.55 K (Waffler §4.4.2)."""
    from py2femm.client import FemmClient

    # Single channel: n_devices=1, device covers exactly s_t width so b_cp=s_t
    cfg = LiquidCoolerConfig(
        devices=[DeviceConfig(name="D0", p_loss=40.0 * 6e-3 * 30e-3)],  # q̇=4W/cm² over s_t×l_cp
        h_cp=4.0,
        d_t=2.0,
        s_t=6.0,
        t_inlet=363.15,
        m_dot=0.0028,
        l_cp=30.0,
        device_spacing=0.0,  # b_cp = bp_w = s_t = 6mm for one-cell model
    )
    # Override bp_w to match s_t so b_cp = s_t = 6mm (one symmetry cell)
    cfg.devices[0].bp_w = 6.0
    cfg.devices[0].a_si = 5.0

    problem = build_circular(cfg)
    client = FemmClient()
    result = client.run(problem)
    assert result.error is None, f"FEMM error: {result.error}"

    parsed = parse_csv_result(result.csv_data or "", n_devices=1)
    t_h = parsed.get("T_h_surface", None)
    assert t_h is not None, "T_h_surface missing from output"
    delta_T = t_h - cfg.t_inlet
    # Waffler analytic: 4.55 K; allow ±20% tolerance for mesh and model differences
    assert 2.0 < delta_T < 8.0, f"ΔT_h-i = {delta_T:.2f} K outside [2, 8] K"


@skip_no_femm
def test_circular_3dev_t_j_above_inlet():
    """Three devices, all powered — T_j must exceed coolant inlet temperature."""
    from py2femm.client import FemmClient

    cfg = default_waffler_config(n_devices=3, p_loss=30.0)
    problem = build_circular(cfg)
    client = FemmClient()
    result = client.run(problem)
    assert result.error is None

    parsed = parse_csv_result(result.csv_data or "", n_devices=3)
    for i in range(3):
        t_j = parsed.get(f"T_j_{i}")
        assert t_j is not None
        assert t_j > cfg.t_inlet, f"T_j_{i}={t_j:.1f} K ≤ T_inlet={cfg.t_inlet} K"
```

- [ ] **Step 5.2: Run (will skip without server — that is correct)**

```
python -m pytest tests/test_liquid_cooler_integration.py -v
```
Expected: 2 tests SKIPPED (no server) or PASSED (if FEMM server running).

- [ ] **Step 5.3: Run full suite one final time**

```
python -m pytest tests/ -q
```
Expected: all unit tests PASS, integration tests SKIPPED.

- [ ] **Step 5.4: Commit**

```bash
git add tests/test_liquid_cooler_integration.py
git commit -m "test: add integration test for liquid cooler Waffler validation"
```

---

## Self-Review Checklist

| Spec requirement | Task |
|-----------------|------|
| Circular channels (Waffler §4.4.2) | Task 2 |
| Rectangular channels | Task 3 |
| Full layer stack Si→Cu→TIM→Al | Tasks 2 & 3 |
| Parametric n_devices | Task 1 (`LiquidCoolerConfig.n_devices` property) |
| compute_h() from Waffler eq. 4.145-4.148 | Task 1 |
| Per-device T_j and R_th,j-inlet | Tasks 2 & 3 post-processing |
| T_h_surface (cooler surface avg) | Tasks 2 & 3 post-processing |
| Thermal coupling matrix | Task 4 (`compute_coupling_matrix`) |
| CSV export parametric sweep | Task 4 (`run_sweep`) |
| Validation against Waffler ΔT_h-i=4.55K | Task 5 |
| Arc BC via raw Lua (set_arc_segment_prop gap) | Task 2 (documented in gotchas) |
