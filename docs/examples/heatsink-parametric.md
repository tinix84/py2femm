# Heat Sink Parametric Study

This example performs a full factorial parametric sweep over heat sink fin geometry, evaluating approximately 176 valid configurations in FEMM to map the design space.

**Source files:**

- Script: `examples/heatflow/heatsink/heatsink_parametric.py`
- Notebook: `examples/heatflow/heatsink/heatsink_parametric.ipynb`

---

## Square-wave parametrization

The heat sink cross-section is described by four independent parameters using a square-wave analogy:

| Parameter | Symbol | Description | Values |
|-----------|--------|-------------|--------|
| Base width | L | Total heatsink width | 4, 8, 12, 16, 20, 24, 28, 32, 36, 40 mm |
| Pitch ratio | p/L | Fin repetition distance as fraction of L | 0.25, 0.50, 0.75 |
| Duty cycle | D | Fraction of pitch occupied by fin | 0.1, 0.25, 0.5 |
| Base ratio | r_b | Base height as fraction of total height | 0.1, 0.25, 0.5, 0.75 |

Fixed parameters: total height H_tot = 25 mm, contact width = 4 mm, P = 10 W, h = 10 W/(m^2*K), T_amb = 298 K.

### Derived quantities

From the four primary parameters, all dimensions are computed:

```python
n_fins = max(2, round(L / pitch))
pitch_actual = L / n_fins
fin_width = D * pitch_actual
gap = (1 - D) * pitch_actual
base_height = r_b * H_tot
fin_height = (1 - r_b) * H_tot
```

---

## Configuration dataclass

```python
@dataclass
class HeatsinkConfig:
    base_width: float      # L
    pitch: float           # p
    duty_cycle: float      # D
    base_ratio: float      # r_b
    height_total: float = 25.0
    contact_width: float = 4.0

    n_fins: int = field(init=False)        # computed
    fin_width: float = field(init=False)   # computed
    gap: float = field(init=False)         # computed
```

---

## Sweep grid

The full factorial produces 10 x 3 x 3 x 4 = 360 combinations. After filtering for manufacturability (fin width >= 2 mm, gap >= 2 mm, at least 2 fins), approximately 176 valid configurations remain.

```python
configs = build_sweep_grid()
print(f"{len(configs)} valid configurations")
# Output: 176 valid configurations
```

---

## Running the sweep

```python
from py2femm.client import FemmClient

client = FemmClient(mode="remote", url="http://localhost:8082")
df = run_sweep(configs, client, timeout=120)
```

Each configuration:

1. Builds the outline nodes (closed polygon with fin zigzag)
2. Creates the FEMM problem (material, BCs, analysis, post-processing)
3. Submits to the server and parses the result
4. Extracts T_avg, T_max, T_min, R_th, A_cross

!!! note "Runtime"
    With 176 configurations at approximately 3 seconds each, the full sweep takes about 10 minutes.

---

## Output DataFrame

The resulting DataFrame has one row per configuration:

| Column | Description |
|--------|-------------|
| `base_width` | L [mm] |
| `pitch_ratio` | p/L |
| `duty_cycle` | D |
| `base_ratio` | r_b |
| `n_fins` | Number of fins |
| `fin_width` | Fin width [mm] |
| `gap` | Gap between fins [mm] |
| `base_height` | Base height [mm] |
| `fin_height` | Fin height [mm] |
| `T_avg` | Average temperature [K] |
| `T_max` | Max temperature (contact) [K] |
| `T_min` | Min temperature (fin tip) [K] |
| `R_th` | Thermal resistance [K/W] |
| `A_cross` | Cross-section area [mm^2] |
| `R_th_per_area` | R_th normalized by area |

---

## Visualizations

### Sensitivity plots

1D line plots showing R_th and A_cross vs each parameter while holding others at nominal values (L=20, p/L=0.50, D=0.25, r_b=0.25):

```python
from heatsink_parametric import plot_sensitivity

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, param in zip(axes.flat, ["base_width", "pitch_ratio", "duty_cycle", "base_ratio"]):
    plot_sensitivity(df, param, ax=ax)
```

### Heatmaps

2D heatmaps of R_th over pitch_ratio vs duty_cycle, faceted by base_width (L) and base_ratio (r_b):

```python
from heatsink_parametric import plot_heatmap

fig = plot_heatmap(df, x_param="pitch_ratio", y_param="duty_cycle",
                   L_values=[12, 20, 32, 40])
```

Grey cells indicate invalid or missing configurations.

### Scaling plot

Best R_th achievable at each base width, showing the fundamental tradeoff between thermal resistance and material usage:

```python
from heatsink_parametric import plot_scaling

fig = plot_scaling(df)
```

### Geometry overlay

Overlay the cross-sections of the top-N configurations to visualize what optimal geometries look like:

```python
from heatsink_parametric import plot_geometry_overlay

top5 = df.nsmallest(5, "R_th")
configs_top5 = [configs[i] for i in top5.index]
fig = plot_geometry_overlay(configs_top5)
```

### Contact mode comparison

Compare centered, single-fin-aligned, and between-fins contact placement:

```python
from heatsink_parametric import plot_contact_comparison

results = {"centered": df_centered, "single_fin": df_single, "between_fins": df_between}
fig = plot_contact_comparison(results)
```

---

## Key findings

Typical observations from the sweep:

- **Base width (L)**: R_th drops sharply as L increases from 4 to 20 mm, then plateaus. Diminishing returns beyond 30 mm.
- **Pitch ratio (p/L)**: Moderate pitch (p/L = 0.50) tends to optimize for most configurations.
- **Duty cycle (D)**: Lower duty cycles (thinner fins, wider gaps) improve convection access but reduce conduction paths. D = 0.25 is often a good tradeoff.
- **Base ratio (r_b)**: Thin bases (r_b = 0.10-0.25) maximize fin height and convection area.

---

## Running the example

```bash
# Script with server already running
python examples/heatflow/heatsink/heatsink_parametric.py

# Auto-start server
python examples/heatflow/heatsink/heatsink_parametric.py --start-server
```

Or use the notebook for interactive exploration:

```bash
jupyter notebook examples/heatflow/heatsink/heatsink_parametric.ipynb
```

---

## Next steps

- [Heat Sink Tutorial](heatsink-baseline.md) -- single-configuration baseline for validation
- [Chip Placement Optimization](optimization.md) -- optimize heat source position
- [Parametric Studies Guide](../guide/parametric.md) -- write your own sweeps
