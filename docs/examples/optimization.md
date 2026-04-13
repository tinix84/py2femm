# Chip Placement Optimization

This example finds the optimal positions of two heat sources (chips) on a rectangular heat sink to minimize a weighted sum of thermal resistances, using both brute-force grid search and scipy Nelder-Mead optimization.

**Source files:**

- Script: `examples/heatflow/heatsink/heatsink_optimize.py`
- Notebook: `examples/heatflow/heatsink/heatsink_optimize.ipynb`

---

## Problem formulation

### Objective

Minimize:

```
f(x_A, x_B) = w_A * R_th_A + w_B * R_th_B
```

where R_th_i = (T_i - T_amb) / P_i is the thermal resistance from chip i to ambient.

### Decision variables

| Variable | Description |
|----------|-------------|
| x_A | Horizontal position of chip A [mm] |
| x_B | Horizontal position of chip B [mm] |

The y-positions are fixed at y = 0 (bottom surface) since this is a 2D planar problem.

### Constraints

- Each chip stays inside the base with a margin >= `min_border_gap` (5 mm)
- Chips do not overlap: edge-to-edge distance >= `min_chip_gap` (5 mm)

---

## Configuration

```python
@dataclass
class ChipConfig:
    name: str = "ChipA"
    width: float = 10.0     # mm
    height: float = 10.0    # mm
    power: float = 5.0      # W

@dataclass
class HeatsinkConfig:
    base_w: float = 210.0   # mm (cross-section width)
    base_h: float = 297.0   # mm (plate length = extrusion depth)
    base_t: float = 5.0     # mm (base thickness)
    n_fins: int = 20
    fin_w: float = 3.0      # mm
    fin_h: float = 20.0     # mm
    k_alu: float = 200.0    # W/(m*K)
    h_conv: float = 10.0    # W/(m^2*K)
    T_amb: float = 298.0    # K

@dataclass
class OptimConfig:
    chip_a: ChipConfig   # 5W chip
    chip_b: ChipConfig   # 15W chip (asymmetric)
    heatsink: HeatsinkConfig
    weight_a: float = 0.5
    weight_b: float = 0.5
    grid_n: int = 10
    max_iter: int = 50
```

The default setup uses an A4-sized heat sink (210 x 297 mm) with two chips of different power levels (5W and 15W), making the problem asymmetric.

---

## FEMM model

The geometry is a simplified rectangular base plate (no explicit fin modeling). The convection coefficient `h_conv` represents the effective fin-enhanced value.

For each evaluation:

1. Build a rectangle with split bottom edge at each chip contact
2. Apply heat flux BCs at chip positions
3. Apply convection on all other surfaces
4. Solve and extract T_A, T_B at each chip center
5. Compute R_th_A, R_th_B, and the weighted objective

!!! note
    The simplified geometry keeps the mesh small, allowing each solve to complete in seconds. This is essential when the optimizer needs hundreds of evaluations.

---

## Method 1 -- Brute-force grid search

Evaluate all feasible combinations on a uniform grid:

```python
grid_results = brute_force(cfg, client)
```

With `grid_n = 10`, this generates 100 (x_A, x_B) combinations. After filtering infeasible placements (overlapping chips or too close to edges), typically 30-60 evaluations run.

The grid search:

- Maps the full design space
- Identifies the global optimum region
- Provides a starting point for local optimization

---

## Method 2 -- Scipy Nelder-Mead

Refine from the best grid point using derivative-free local optimization:

```python
best_grid = min(grid_results, key=lambda r: r["objective"])
scipy_result = scipy_optimize(
    cfg, client,
    x0=(best_grid["x_a"], best_grid["x_b"])
)
```

Nelder-Mead is a good choice here because:

- The objective function is noisy (numerical simulation)
- No gradients are available
- The design space is 2D (low-dimensional)
- Convergence tolerances: `xatol=1.0` mm, `fatol=0.01` K/W

Infeasible points receive a penalty of 10^6, steering the simplex back into the feasible region.

---

## Visualization

The script produces a 3-panel figure:

### Panel 1 -- Objective function

Scatter plot of (x_A, x_B) colored by the objective value. The best grid point is marked with a red star, and the scipy optimum with a magenta diamond.

### Panel 2 -- Pareto front

R_th_A vs R_th_B scatter plot showing the tradeoff between cooling the two chips. The Pareto front (non-dominated solutions) is traced with a dashed line.

### Panel 3 -- Best placement

Schematic showing the heat sink base, fins, and the optimal chip positions.

---

## Running the example

```bash
# Basic run (requires server)
python examples/heatflow/heatsink/heatsink_optimize.py

# Auto-start server
python examples/heatflow/heatsink/heatsink_optimize.py --start-server

# Customize grid and optimizer
python examples/heatflow/heatsink/heatsink_optimize.py --grid-n 8 --max-iter 30

# Custom chip powers and weights
python examples/heatflow/heatsink/heatsink_optimize.py --power-a 10 --power-b 10 --weight-a 0.5 --weight-b 0.5

# Skip plots and scipy (just grid search)
python examples/heatflow/heatsink/heatsink_optimize.py --no-plot --no-scipy
```

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--start-server` | False | Auto-start py2femm server |
| `--grid-n` | 10 | Grid points per axis |
| `--max-iter` | 50 | Scipy max iterations |
| `--base-w` | 210 | Base width [mm] |
| `--base-h` | 297 | Base height [mm] |
| `--power-a` | 5.0 | Chip A power [W] |
| `--power-b` | 15.0 | Chip B power [W] |
| `--weight-a` | 0.5 | Objective weight for chip A |
| `--weight-b` | 0.5 | Objective weight for chip B |
| `--timeout` | 300 | Seconds per FEMM run |
| `--no-plot` | False | Skip matplotlib plots |
| `--no-scipy` | False | Skip Nelder-Mead refinement |

---

## Extending the optimizer

To optimize different quantities or add more chips:

1. Add more `ChipConfig` entries to `OptimConfig`
2. Extend `build_model()` to place additional heat sources
3. Update `is_feasible()` with new overlap constraints
4. Modify the objective function in `evaluate()`

For higher-dimensional problems (3+ chips, variable chip sizes), consider using a global optimizer (differential evolution, CMA-ES) instead of brute-force + Nelder-Mead.

---

## Next steps

- [Heat Sink Tutorial](heatsink-baseline.md) -- understand the baseline model
- [Heat Sink Parametric](heatsink-parametric.md) -- sweep fin geometry parameters
- [Parametric Studies Guide](../guide/parametric.md) -- build your own optimization loop
