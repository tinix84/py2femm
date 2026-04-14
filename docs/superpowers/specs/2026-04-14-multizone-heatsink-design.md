# Multi-Zone Heatsink Design Spec

**Date:** 2026-04-14
**Issue:** GitHub #1 — Support different thermal coefficient zones on the same heat sink
**Status:** Draft

---

## Problem

Currently py2femm heatsink examples assign a single material and uniform convection across the entire heat sink surface. Real heat sinks often have different zones — denser/taller fins near a high-power component, sparser fins elsewhere, and sometimes a copper heat spreader insert under the hottest chip. A mounting bracket or fixing point may also occupy a zone with minimal fin area.

## Goal

Create a new example (`heatsink_multizone.py`) that demonstrates a heat sink with multiple thermal zones along the x-axis, each with its own material and convection coefficient. The example compares a uniform baseline against an optimized multi-zone layout to show the cost/performance tradeoff.

---

## Data Model

```python
@dataclass
class Zone:
    x_start: float          # left edge [mm]
    x_end: float            # right edge [mm]
    material: str           # e.g. "Aluminum", "Copper"
    kx: float               # thermal conductivity x-direction [W/(m·K)]
    ky: float               # thermal conductivity y-direction [W/(m·K)]
    h_conv: float           # convection coefficient on top surface [W/(m²·K)]

@dataclass
class Chip:
    name: str               # e.g. "ChipA"
    x_center: float         # center position on bottom edge [mm]
    width: float            # contact width [mm]
    power: float            # dissipated power [W]

@dataclass
class MultiZoneConfig:
    zones: list[Zone]       # left-to-right, must tile [0, base_w] contiguously
    chips: list[Chip]       # placed independently of zone boundaries
    base_w: float           # total width [mm] — must equal last zone's x_end
    base_h: float           # total height [mm]
    depth: float = 100.0    # extrusion depth for planar 2D [mm]
    t_ambient: float = 300.0  # ambient/sink temperature [K]
```

**Validation rules:**
- Zones must tile `[0, base_w]` with no gaps or overlaps: `zones[0].x_start == 0`, `zones[-1].x_end == base_w`, and each `zones[i].x_end == zones[i+1].x_start`.
- Each chip contact `[x_center - width/2, x_center + width/2]` must lie within `[0, base_w]`.
- Chips may span zone boundaries — this is physically valid and FEMM handles it naturally.

---

## Geometry

The base plate is a rectangle `[0, base_w] x [0, base_h]` with vertical partition lines at internal zone boundaries.

```
    h=15           h=5          h=50
   ┌───────────┬──────────┬──────────────┐ y = base_h
   │ Aluminum  │ Aluminum │   Copper     │
   │ kx=200    │ kx=200   │   kx=385     │
   │           │(bracket) │              │
   └──┬───┬───┴──────────┴──┬──────┬────┘ y = 0
      │5W │                 │ 15W  │
     ChipA                  ChipB
   x=0   x=60         x=100       x=180
```

### Nodes

1. **Outer corners:** `(0,0)`, `(base_w, 0)`, `(base_w, base_h)`, `(0, base_h)`
2. **Zone boundary endpoints:** For each internal zone boundary at `x_b`: `(x_b, 0)` and `(x_b, base_h)`
3. **Chip contact edges:** For each chip: `(x_center - width/2, 0)` and `(x_center + width/2, 0)`

All bottom-edge nodes are sorted by x and deduplicated (1e-6 tolerance) to handle chips whose edges coincide with zone boundaries.

### Lines

- **Top edge segments:** One per zone, from `(zone.x_start, base_h)` to `(zone.x_end, base_h)`
- **Bottom edge segments:** Split at zone boundaries and chip edges, sorted left-to-right
- **Side walls:** `(0, 0)→(0, base_h)` and `(base_w, 0)→(base_w, base_h)`
- **Internal partition lines:** Vertical lines at each zone boundary `(x_b, 0)→(x_b, base_h)`

### Block Labels

One per zone, placed at `((zone.x_start + zone.x_end) / 2, base_h / 2)`.

### Boundary Conditions

| Surface | BC | Notes |
|---------|-----|-------|
| Top segments | `HeatFlowConvection` per zone | Each zone's `h_conv` and `t_ambient` |
| Chip contacts | `HeatFlowHeatFlux` per chip | `qs = -power / (width * depth * 1e-6)` (negative = inward) |
| Bottom non-contact | No BC assigned | Insulated (zero flux default) |
| Side walls | No BC assigned | Insulated |
| Internal partitions | No BC assigned | Perfect thermal contact (continuity) |

### Materials

One `HeatFlowMaterial` per unique `(material, kx, ky)` tuple. Deduplicated by name — if two zones use "Aluminum" with the same properties, only one material definition is emitted.

---

## Example Scenarios

### Scenario A — Uniform Baseline

| Parameter | Value |
|-----------|-------|
| Base | 180 x 10 mm, depth=100mm |
| Zones | 3 zones, all Aluminum kx=ky=200, all h=25 |
| ChipA | 5W, x=30mm, width=20mm |
| ChipB | 15W, x=140mm, width=30mm |

### Scenario B — Optimized Multi-Zone

| Zone | x range | Material | kx, ky | h_conv | Rationale |
|------|---------|----------|--------|--------|-----------|
| 1 | 0–60mm | Aluminum | 200, 200 | 15 | Sparse fins, low-power chip region |
| 2 | 60–100mm | Aluminum | 200, 200 | 5 | Mounting bracket, minimal fins |
| 3 | 100–180mm | Copper | 385, 385 | 50 | Dense fins + copper spreader under hot chip |

Same chips as Scenario A.

### Comparison Output

For each scenario, extract:
- Temperature at each chip contact center via `ho_getpointvalues(x, 0)`
- Average temperature per zone via `ho_selectblock` / `ho_blockintegral(0)` for each zone's label point
- Thermal resistance per chip: `R_th = (T_chip - T_ambient) / P_chip`

Print a side-by-side comparison table showing the tradeoff: slightly higher temperature on ChipA (fewer fins), significantly lower temperature on ChipB (copper + dense fins).

---

## Post-Processing

The generated Lua script writes results as key-value pairs to `results.csv`:

```
T_ChipA_K = 345.2
T_ChipB_K = 378.4
T_avg_zone_0_K = 340.1
T_avg_zone_1_K = 335.8
T_avg_zone_2_K = 355.3
```

The `parse_results()` function reads this CSV and returns a dict. The comparison logic computes R_th values and prints the formatted table.

---

## File Structure

| File | Purpose |
|------|---------|
| `examples/heatflow/heatsink/heatsink_multizone.py` | Module: dataclasses, geometry builder, FEMM problem builder, parse/compare |
| `tests/test_multizone.py` | Unit tests: config validation, geometry nodes, Lua output checks (no FEMM) |

---

## Testing (Unit — No FEMM Required)

1. **Config validation:** Zones must tile contiguously, chips must fit within base
2. **Geometry correctness:** Correct number of nodes, lines, internal partitions for a 3-zone 2-chip config
3. **Lua output checks:**
   - Correct number of `hi_addmaterial` calls (deduplicated)
   - Correct number of `hi_addblocklabel` calls (one per zone)
   - Top segments get per-zone convection BCs
   - Chip contacts get heat flux BCs
   - Bottom non-contact segments have no BC assigned
   - Internal partition lines have no BC assigned
   - No Lua 4.0 table indexing (`[1]` must not appear)
   - `PY2FEMM_DONE` sentinel present
4. **Chip spanning zone boundary:** A chip whose contact straddles two zones should produce valid geometry without duplicate nodes

---

## Out of Scope

- Partial-height inserts (e.g., copper pad only in bottom 3mm) — requires horizontal partition lines and more complex geometry; natural follow-up
- Automated fin geometry (zigzag nodes) — convection coefficient `h` models the fin effect as a lumped parameter
- Optimization/sweep over zone parameters — the module is reusable for this but the example only runs the two fixed scenarios
- Jupyter notebook — can be added later as a thin wrapper
