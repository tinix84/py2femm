# Design: Heatsink Parametric Study with Square-Wave Fin Parametrization

**Date:** 2026-04-12
**Status:** Draft
**Author:** tinix84 + Claude

## Problem Statement

The existing `heatsink_tutorial` reproduces the FEMM Tutorial #7 (steady-state heat flow) but:

1. **Temperature mismatch:** Code gives T_avg ≈ 334K vs expected ~356K from the video tutorial — caused by convection applied to bottom surface segments that should be insulated.
2. **No FEMM visualization:** The notebook only shows a rough matplotlib approximation of the temperature field, not the actual FEMM contour plot (fins appear same color as base).
3. **Limited parametric study:** Current sweep only varies fin count (3, 5, 7, 9) with fixed fin dimensions. No exploration of fin shape, base proportions, or heatsink width.

## Goals

1. **Notebook 1 (`heatsink_baseline.ipynb`):** Fix the BC mismatch, add FEMM bitmap capture, remove the parametric sweep.
2. **Notebook 2 (`heatsink_parametric.ipynb`):** Full parametric study using a square-wave analogy to parametrize fin geometry, with L-grouped factorial sweep and rich visualization.

## Square-Wave Parametrization

The heatsink cross-section is modeled like a periodic square wave:

### Primary parameters

| Symbol | Code name | Description | Unit |
|--------|-----------|-------------|------|
| `L` | `base_width` | Total heatsink width | mm |
| `p` | `pitch` | Fin repetition distance (target) | mm |
| `D` | `duty_cycle` | Fraction of pitch occupied by fin [0–1] | — |
| `r_b` | `base_ratio` | Base height fraction: `H_b / H_tot` [0–1] | — |
| `H_tot` | `height_total` | Total height = base + fin (fixed 25 mm) | mm |

### Derived quantities

| Symbol | Expression | Description |
|--------|------------|-------------|
| `n` | `max(2, round(L / p))` | Number of fins |
| `p_actual` | `L / n` | Actual pitch (adjusted to fill L exactly) |
| `w_f` | `D × p_actual` | Fin width |
| `g` | `(1 − D) × p_actual` | Gap between fins |
| `H_b` | `r_b × H_tot` | Base height |
| `H_f` | `(1 − r_b) × H_tot` | Fin height |

### Parameter grid

| Parameter | Expression | Values |
|-----------|------------|--------|
| `L` | `[1..10] × source_width` (source_width = 4 mm) | {4, 8, 12, 16, 20, 24, 28, 32, 36, 40} mm |
| `pitch/L` | ratio | {0.25, 0.50, 0.75} |
| `D` | duty cycle | {0.1, 0.25, 0.5} |
| `r_b` | `H_b / H_tot` | {0.1, 0.25, 0.5, 0.75} |

Full factorial: 10 × 3 × 3 × 4 = 360 combinations.

### Validity constraints

A configuration is valid if **all** of:
- `w_f >= 2 mm` (fin manufacturable)
- `g >= 2 mm` (gap manufacturable)
- `n >= 2` (at least 2 fins)

After filtering: estimated ~150–200 valid runs ≈ 10–13 min at ~4 s/run.

### Contact patch

- Fixed width: 4 mm, always on the base bottom
- Three alignment modes (parameter `contact_mode`):
  - `"centered"` — centered on base (default, used for main sweep)
  - `"single_fin"` — shifted to align with nearest fin center
  - `"between_fins"` — shifted to midpoint between two central fins
- Contact mode is a **separate comparison** (not part of main factorial). Run main sweep with `"centered"`, then re-run top-5 configs with all 3 modes.

## Thermal Setup (unchanged from tutorial)

- Material: Aluminum (k = 200 W/m·K)
- Power: P = 10 W on 4 mm contact patch
- Heat flux: qs = P / (contact_width × depth × 1e-6) = 25000 W/m²
- Convection: h = 10 W/(m²·K), T_amb = 298 K
- Depth: 100 mm (planar extrusion)
- **Boundary conditions:**
  - Contact patch: heat flux
  - Bottom segments (y=0, not contact): **insulated** (no BC assigned)
  - All other segments (fins, sides, top): convection

## Output Metrics

For each valid configuration, extracted from FEMM:

| Metric | Source | Description |
|--------|--------|-------------|
| `T_avg` | `ho_blockintegral(0)` on whole block | Overall average temperature [K] |
| `T_max` | `ho_getpointvalues(contact_center_x, 0)` | Hottest point [K] |
| `T_min` | `ho_getpointvalues(outermost_fin_tip_x, H_b + H_f)` | Coldest point [K] |
| `R_th` | `(T_avg − T_amb) / P` | Thermal resistance [K/W] |
| `A_cross` | `L × H_b + n × w_f × H_f` | Cross-section area [mm²] |
| `R_th_per_area` | `R_th / A_cross` | Efficiency metric [K/W/mm²] |

### Future enhancement (not this iteration)

Split geometry into separate blocks (base + individual fins via internal lines at y=H_b) to get:
- `T_avg_base`: average base temperature
- `T_avg_fin[i]`: per-fin average (left→right), showing thermal gradient and "starved" outer fins

## File Structure

| File | Role |
|------|------|
| `heatsink_tutorial.py` | Shared backend — geometry, FEMM problem, parsing, server utils, bitmap capture |
| `heatsink_parametric.py` | New — square-wave parametrization, sweep engine, parametric plotting |
| `heatsink_baseline.ipynb` | Renamed notebook 1 — FEMM tutorial #7 reproduction |
| `heatsink_parametric.ipynb` | New notebook 2 — parametric study |
| `heatsink_optimize.py` | Unchanged — 2-chip optimizer (separate concern) |
| `heatsink_optimize.ipynb` | Unchanged |
| `heatsink.py` | Unchanged — original standalone script |

## Changes to `heatsink_tutorial.py`

### Fix: convection BC assignment

Skip convection on bottom segments where both endpoints have `y == 0` and the segment is not the contact patch. In FEMM, unassigned segments default to insulated (zero flux). This should bring T_avg from ~334K to ~356K, matching the tutorial video.

### Add: FEMM bitmap capture

New Lua commands appended after analysis:
```lua
ho_showdensityplot(0, 0, T_min, T_max, "temperature")
ho_save_bitmap("heatsink_temperature.bmp")
```

New Python helper to display the image in notebooks:
```python
def load_femm_bitmap(workspace_path: str) -> np.ndarray:
    """Read BMP from FEMM workspace, return as numpy array for plt.imshow()."""
```

### Remove: parametric sweep (section 9)

Functions `build_parametric()`, `run_parametric()`, `plot_parametric()` removed — superseded by notebook 2.

The `--no-parametric` CLI flag is also removed from `main()`.

## `heatsink_parametric.py` API

```python
@dataclass
class HeatsinkConfig:
    base_width: float       # L [mm]
    pitch: float            # p target [mm]
    duty_cycle: float       # D [0-1]
    base_ratio: float       # r_b = H_b / H_tot
    height_total: float = 25.0
    contact_width: float = 4.0
    contact_mode: str = "centered"

    # Derived (computed in __post_init__)
    n_fins: int
    pitch_actual: float
    fin_width: float
    gap: float
    base_height: float
    fin_height: float

def is_valid(cfg: HeatsinkConfig) -> bool:
    """Check fin_width >= 2mm, gap >= 2mm, n_fins >= 2."""

def build_sweep_grid() -> list[HeatsinkConfig]:
    """Generate all valid configs from the full parameter grid."""

def build_femm_problem(cfg: HeatsinkConfig) -> str:
    """Build geometry + FEMM problem from config, return Lua script."""

def run_sweep(configs: list[HeatsinkConfig], client) -> pd.DataFrame:
    """Run all configs via FEMM, return DataFrame with params + metrics."""

# --- Plotting ---
def plot_sensitivity(df, param_name, ...):
    """1D line plot: R_th vs one param, others at nominal."""

def plot_heatmap(df, x_param, y_param, ...):
    """2D heatmap: R_th over (x_param vs y_param)."""

def plot_scaling(df, ...):
    """R_th and A_cross vs L at best config per L."""

def plot_contact_comparison(df_centered, df_single, df_between, ...):
    """Side-by-side comparison of contact alignment modes."""

def plot_geometry_overlay(configs: list[HeatsinkConfig], ...):
    """Overlay top-N cross-sections with different colors."""
```

## Notebook 2 Cell Flow

| Cell | Content |
|------|---------|
| 0 | Imports, server health check |
| 1 | Define parameter grid, filter to valid, show count + preview table |
| 2 | Run sweep with progress output (~10 min) |
| 3 | Results DataFrame display (sortable by R_th) |
| 4 | 1D sensitivity: 4 subplots, one per param (R_th + A_cross on twin y-axes) |
| 5 | 2D heatmaps: grid of (pitch/L vs D) colored by R_th, rows = r_b, cols = representative L values |
| 6 | Scaling plot: R_th and A_cross vs L at best config per L |
| 7 | Contact mode comparison: re-run top-5 with all 3 modes, bar chart |
| 8 | Best configs summary table + geometry overlay of top-3 |

## Notebook 1 Cell Flow (revised)

| Cell | Content |
|------|---------|
| 0 | Imports, server health check |
| 1 | Dimensions printout + geometry build + plot |
| 2 | Build FEMM problem + run (5-fin baseline) |
| 3 | Parse results: T_avg, R_th, point values |
| 4 | FEMM temperature contour image (bitmap loaded from workspace) |
| 5 | Summary bar chart (T_ambient, T_avg, ΔT, R_th) |

## Sweep Strategy: L-Grouped Factorial (Approach C)

Results are organized by `L` (base width), which is the "scale" parameter. Within each L, the `pitch/L × D × r_b` grid defines the fin pattern shape.

**Visualization hierarchy:**
1. **Per-L dashboards** — for each L: heatmap of R_th over (pitch/L, D) at each r_b
2. **Scaling plot** — R_th vs L at the best (pitch/L, D, r_b) per L, showing diminishing returns
3. **Cross-comparison** — best config per L on a R_th vs A_cross scatter

**Nominal values** for 1D sensitivity plots: L=20mm, pitch/L=0.5, D=0.25, r_b=0.25.

## Risk / Open Questions

- **FEMM bitmap path:** The executor creates job directories under the workspace (e.g., `workspace/job_<uuid>/`). The Lua script runs with CWD = job directory, so `ho_savebitmap("heatsink_temperature.bmp")` saves there. The notebook reads it back from that known path. Since the server runs on localhost, file access is direct.
- **ho_savebitmap vs ho_save_bitmap:** FEMM 4.2 official Lua reference uses `ho_savebitmap(filename)` (no underscore). The existing `femm_problem.py` code uses `ho_save_bitmap()`. Verify which works at implementation time; may need to fix the existing code too.
- **ho_showdensityplot signature:** `ho_showdensityplot(legend, gscale, upper_T, lower_T, type)` where `type=0` is temperature. The `legend` and `gscale` args control legend visibility and greyscale; use `(1, 0, T_max, T_min, 0)` for color temperature plot with legend.
- **Small-L invalidity:** Many L=4mm and L=8mm combinations will be filtered (pitch too small for 2mm constraints). This is expected and shown in the notebook as grey/hatched cells in heatmaps.
- **Run time estimate:** ~150–200 valid runs × ~4s = 10–13 min. Contact mode comparison adds ~15 runs (top-5 × 3 modes) = ~1 min extra.
- **Sweep progress:** Print one line per run (`"[23/187] L=20mm, pitch/L=0.50, D=0.25, r_b=0.25 → R_th=3.62 K/W"`) so the user can monitor progress during the ~10 min sweep.
