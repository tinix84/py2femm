# Liquid-Cooled Heatsink for TO-247 — 2D FEMM Example Design

**Date:** 2026-04-18  
**Reference:** Waffler, S. *Bidirectional DC-DC Converter for Vehicle Applications*, ETH Zurich Diss. 2011, §4.4 (pp. 263–273)

---

## Overview

A py2femm example that models the 2D cross-section of a liquid-cooled aluminium plate carrying multiple TO-247 power semiconductor packages. The example reproduces the finite element simulation in Waffler Fig. 4.46 and extends it to a full junction-to-coolant thermal stack with parametric device count.

Two separate builder functions share a common config dataclass: one for circular drilled channels (Waffler geometry) and one for rectangular milled channels (simpler, parametric-friendly). A sweep script drives both and exports results as CSV.

---

## Scope

| Feature | Included |
|---------|----------|
| Circular channel cross-section (Waffler Fig. 4.46 reproduction) | ✓ |
| Rectangular channel cross-section | ✓ |
| Full layer stack: Si die → Cu baseplate → TIM → Al cooler | ✓ |
| Parametric `n_devices` TO-247 packages on one plate | ✓ |
| Per-device junction temperature and R_th,j-inlet | ✓ |
| Thermal coupling matrix between devices | ✓ |
| CSV export for parametric sweep | ✓ |
| Jupyter notebook with plots | ✓ |
| Dynamic fluid simulation (CFD) | ✗ — h computed analytically |
| 3D effects / axisymmetric | ✗ — planar 2D only |

---

## File Structure

```
examples/heatflow/liquid_cooler_to247/
  config.py            # dataclasses + compute_h() + default_waffler_config()
  circular.py          # build_circular(cfg) → FemmProblem
  rectangular.py       # build_rectangular(cfg) → FemmProblem
  sweep.py             # parametric loop → results CSV
  liquid_cooler.ipynb  # notebook: run both, plot, coupling matrix heatmap
```

---

## Geometry

**Physics:** planar heat flow, units = mm, depth = `l_cp` (cooler length, mm).

### Cross-section layer stack (bottom to top)

```
  [Si die: a_si × a_si mm,  q̇ = P_loss / a_si²]   ← one per device
  [Cu baseplate: bp_w × h_cu mm                  ]   ← spreading layer
  [TIM: bp_w × d_tim mm,  λ = k_tim              ]   ← main R_th bottleneck
  [Al cooler block: b_cp × h_cp mm               ]   ← with channels
       (○ circular  or  [□] rectangular channels)
  insulated bottom
```

### Cooler block geometry

**Circular channels (Waffler):**  
- Channel diameter: `d_t` centred vertically at `h_cp / 2`  
- Pitch: `s_t` (one channel per pitch cell)  
- Total cooler width: `b_cp = n_channels × s_t`, where `n_channels` covers all devices  
- FEMM geometry: rectangular block with `CircleArc` cutouts (two 180° arcs per channel)

**Rectangular channels:**  
- Channel width: `ch_w`, height: `ch_h`, fin wall width: `fin_w`  
- Channels open at bottom (or closed — configurable)  
- FEMM geometry: purely `Node` / `Line` — no arcs required

### Device placement

Cooler width is determined by device count and spacing:

```
device_pitch = bp_w + device_spacing   # mm — baseplate width + gap
b_cp         = n_devices * device_pitch
n_channels   = ceil(b_cp / s_t)        # circular channels to cover full width
```

Device `i` (0-indexed) has its baseplate left edge at `i * device_pitch`, centred at:

```
x_center[i] = i * device_pitch + bp_w / 2
```

Si die is centred on the baseplate; offset `(bp_w - a_si) / 2` from each side.

---

## Default Parameters (Waffler §4.4)

| Symbol | Parameter | Default | Source |
|--------|-----------|---------|--------|
| `h_cp` | Cooler height | 4 mm | Waffler §4.4.2 |
| `d_t` | Channel diameter | 2 mm | Waffler §4.4.2 |
| `s_t` | Channel pitch | 6 mm | Waffler §4.4.2 |
| `d_tim` | TIM thickness | 0.2 mm | Waffler §4.4.1 |
| `k_tim` | TIM conductivity | 2 W/mK | Waffler §4.4.1 |
| `h_cu` | Cu baseplate height | 3 mm | TO-247 package |
| `bp_w` | Cu baseplate width | 15 mm | TO-247 package |
| `a_si` | Si die side length | 5 mm | Waffler eq. 4.138 |
| `n_devices` | Number of TO-247 | 3 | parametric |
| `t_inlet` | Coolant inlet temperature | 363 K (90°C) | Waffler §4.4 |
| `p_loss` | Power per device | 30 W | example default |
| `l_cp` | Cooler depth (extrusion) | 30 mm | example default |

---

## Materials

| Region | Material name | kx = ky (W/mK) | Note |
|--------|--------------|----------------|------|
| Si die | `Silicon` | 130 | heat source region |
| Cu baseplate | `Copper` | 385 | spreading layer |
| TIM | `ThermalPad` | `k_tim` | configurable |
| Al cooler | `Aluminum` | 160 | Waffler Tab. 4.16 at 90°C |

One `HeatFlowMaterial` + `define_block_label()` per region. Block labels placed at region centroids.

---

## Boundary Conditions

| Surface | BC type | Value | Note |
|---------|---------|-------|------|
| Top of each Si die | `HeatFlowHeatFlux` | `qs = -P_loss / a_si²` | negative = into domain |
| Channel walls (circle arcs or rect segments) | `HeatFlowConvection` | `h`, `T_inf = t_inlet` | one BC object, applied to all channel walls |
| All other external surfaces | default (zero flux) | — | FEMM default = insulated |

The convective coefficient `h` is computed by `compute_h(cfg)` in `config.py` using Waffler eq. 4.145–4.147 (Nusselt correlation for laminar/turbulent pipe flow):

```
Re = 4 * m_dot / (pi * eta_f * d_t)      # eta_f = dynamic viscosity [Pa·s]
Nu = Nusselt(Re, Pr, d_t, l_cp)          # eq. 4.146/4.147/4.148
h  = Nu * lambda_f / d_t
```

For Waffler defaults (ṁ=300 l/h per channel, water at 90°C): **h ≈ 9 436 W/m²K**.

---

## Post-Processing

All post-processing is raw Lua appended to `problem.lua_script`.

### Per device (device index `i`)

```lua
-- junction temperature (top surface of Si die)
T_j_i = ho_getpointvalues(x_die_center_i, y_die_top)
write(file_out, "T_j_", i, " = ", T_j_i, "\n")

-- case temperature (bottom of Cu baseplate = top of TIM)
T_case_i = ho_getpointvalues(x_bp_center_i, y_tim_top)
write(file_out, "T_case_", i, " = ", T_case_i, "\n")
```

### Cooler surface

```lua
-- average cooler top surface temperature (ho_blockintegral(0) = avg T directly)
ho_selectblock(b_cp/2, h_cp - 0.1)
T_h = ho_blockintegral(0)
ho_clearblock()
write(file_out, "T_h_surface = ", T_h, "\n")
```

### Thermal resistance (Python side)

```python
R_th_j_inlet[i] = (T_j[i] - cfg.t_inlet) / cfg.p_loss[i]
```

### Thermal coupling matrix

`sweep.py` runs `n_devices` separate FEMM jobs. In job `k`, only device `k` is powered (`p_loss[k] > 0`, all others = 0). After each run, `T_j[i]` is read for all devices. The coupling coefficient is:

```python
C[k][i] = (T_j[i] - cfg.t_inlet) / cfg.p_loss[k]  # K/W
```

`C` is an `n_devices × n_devices` matrix. Diagonal entries are self-heating R_th; off-diagonal entries are mutual thermal impedances.

---

## Sweep Script (`sweep.py`)

Parametric variables (all others held at defaults):

| Variable | Range | Steps |
|----------|-------|-------|
| `n_devices` | 1 – 5 | 5 |
| `device_spacing` | 0 – 10 mm (gap between baseplates) | 6 |
| `p_loss` | 10 – 50 W/device | 5 |

For each combination, runs both circular and rectangular builders. Writes one CSV row per combination. Total runs: at most `5 × 6 × 5 × 2 = 300` (prunable by user).

---

## Validation Target

For the single-device circular case with Waffler defaults:

| Quantity | Waffler analytic | Target FEMM result |
|----------|------------------|--------------------|
| ΔT_h-w (Al conduction) | 0.4 K | < 0.5 K |
| ΔT_w-f (channel convection) | 4.05 K | 3.8 – 4.3 K |
| ΔT_h-i (total cooler) | 4.55 K | ± 10% |

---

## Config Dataclasses (`config.py`)

```python
@dataclass
class DeviceConfig:
    name: str
    p_loss: float        # W
    a_si: float          # mm — Si die side length
    bp_w: float          # mm — Cu baseplate width
    h_cu: float          # mm — Cu baseplate height
    d_tim: float         # mm — TIM thickness
    k_tim: float         # W/mK

@dataclass
class LiquidCoolerConfig:
    devices: list[DeviceConfig]
    h_cp: float          # mm — cooler height
    d_t: float           # mm — circular channel diameter
    s_t: float           # mm — channel pitch
    ch_w: float          # mm — rectangular channel width
    ch_h: float          # mm — rectangular channel height
    fin_w: float         # mm — fin wall width (rect channels)
    t_inlet: float       # K  — coolant inlet temperature
    m_dot: float         # kg/s — mass flow rate per channel
    l_cp: float          # mm — cooler depth (extrusion)

def compute_h(cfg: LiquidCoolerConfig) -> float:
    """Return convective coefficient [W/m²K] from Waffler eq. 4.145-4.148."""
    ...

def default_waffler_config(n_devices: int = 3) -> LiquidCoolerConfig:
    """Return config reproducing Waffler §4.4.2 geometry."""
    ...
```

---

## Gotchas

- **CircleArc in FEMM Lua 4.0:** use `hi_addarc(x1,y1,x2,y2,angle,maxseg)` — not table indexing on return values.
- **Block label placement:** Si die label must be strictly inside the die rectangle, not on its edge. Use centroid `(x_center, y_die_bottom + a_si/2)`.
- **Channel void regions:** circular/rectangular channel interiors must NOT have a block label — FEMM treats unlabelled regions as void (no conduction), which is correct for the fluid domain (convection handled by BC on wall).
- **Zero-flux default:** FEMM segments with no BC assigned default to zero flux (insulated). The gaps between device baseplates on the cooler top surface need no explicit BC.
- **Deduplication:** when building the rectangular channel polygon outline, deduplicate consecutive nodes with 1e-6 tolerance (see `heatsink.py`).
