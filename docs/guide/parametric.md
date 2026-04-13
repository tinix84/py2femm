# Parametric Studies

py2femm supports running parametric sweeps where you vary geometry, material, or boundary parameters across many configurations and collect results in a DataFrame.

---

## The sweep pattern

The reference implementation in `heatsink_parametric.py` follows a three-part pattern:

1. **Config dataclass** -- parametrize the design
2. **Grid builder** -- generate all valid combinations
3. **Sweep engine** -- run each config in FEMM and collect results

---

## 1. Configuration dataclass

Define a dataclass that captures the full design space:

```python
from dataclasses import dataclass, field

@dataclass
class HeatsinkConfig:
    base_width: float       # L -- total width [mm]
    pitch: float            # p -- fin repetition distance [mm]
    duty_cycle: float       # D -- fraction of pitch occupied by fin [0-1]
    base_ratio: float       # r_b -- base height as fraction of total height

    # Fixed parameters
    height_total: float = 25.0
    contact_width: float = 4.0

    # Derived (computed in __post_init__)
    n_fins: int = field(init=False)
    fin_width: float = field(init=False)
    gap: float = field(init=False)

    def __post_init__(self):
        self.n_fins = max(2, round(self.base_width / self.pitch))
        self.pitch_actual = self.base_width / self.n_fins
        self.fin_width = self.duty_cycle * self.pitch_actual
        self.gap = (1 - self.duty_cycle) * self.pitch_actual
```

Use `__post_init__` to compute derived quantities. This keeps the parameter space minimal while making all dimensions available.

---

## 2. Grid builder

Generate all valid combinations using `itertools.product`:

```python
from itertools import product

L_VALUES = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40]
PITCH_RATIOS = [0.25, 0.50, 0.75]
DUTY_CYCLES = [0.1, 0.25, 0.5]
BASE_RATIOS = [0.1, 0.25, 0.5, 0.75]

def is_valid(cfg: HeatsinkConfig) -> bool:
    """Manufacturability: min 2mm fin width, min 2mm gap."""
    return cfg.fin_width >= 2.0 and cfg.gap >= 2.0 and cfg.n_fins >= 2

def build_sweep_grid() -> list[HeatsinkConfig]:
    configs = []
    for L, pr, D, rb in product(L_VALUES, PITCH_RATIOS, DUTY_CYCLES, BASE_RATIOS):
        pitch = pr * L
        cfg = HeatsinkConfig(base_width=L, pitch=pitch, duty_cycle=D, base_ratio=rb)
        if is_valid(cfg):
            configs.append(cfg)
    return configs
```

The full factorial grid (10 x 3 x 3 x 4 = 360) filters down to approximately 176 valid configurations after applying manufacturability constraints.

---

## 3. Sweep engine

Run all configurations and collect results:

```python
import pandas as pd
from py2femm.client import FemmClient

def run_sweep(configs: list[HeatsinkConfig], client: FemmClient,
              timeout: int = 120) -> pd.DataFrame:
    rows = []
    for idx, cfg in enumerate(configs):
        print(f"[{idx+1}/{len(configs)}] L={cfg.base_width:.0f}mm", end=" ")

        lua = build_femm_problem(cfg)  # returns Lua script string
        result = client.run(lua, timeout=timeout)

        if result.error or not result.csv_data:
            print(f"FAILED: {result.error}")
            continue

        parsed = parse_results(result.csv_data)
        T_avg = parsed.get("AverageTemperature_K")
        if T_avg is None:
            continue

        R_th = (T_avg - 298.0) / 10.0  # thermal resistance
        rows.append({
            "base_width": cfg.base_width,
            "duty_cycle": cfg.duty_cycle,
            "T_avg": T_avg,
            "R_th": R_th,
            # ... more columns
        })
        print(f"-> R_th={R_th:.2f} K/W")

    return pd.DataFrame(rows)
```

---

## Writing your own sweep

To create a parametric study for a different problem:

### Step 1 -- Define your config

```python
@dataclass
class MotorConfig:
    slot_depth: float
    magnet_thickness: float
    air_gap: float
    # ...
```

### Step 2 -- Write the FEMM builder

```python
def build_motor_problem(cfg: MotorConfig) -> str:
    problem = FemmProblem(out_file="motor_results.csv")
    problem.magnetic_problem(freq=0, unit=LengthUnit.MILLIMETERS, type="planar")
    # ... build geometry from cfg ...
    # ... add materials, BCs, analysis ...
    problem.close()
    return "\n".join(problem.lua_script)
```

### Step 3 -- Run the sweep

```python
configs = [MotorConfig(sd, mt, ag)
           for sd in [10, 15, 20]
           for mt in [3, 5, 7]
           for ag in [0.5, 1.0]]

client = FemmClient(mode="remote", url="http://localhost:8082")
df = run_sweep(configs, client)
```

---

## Performance considerations

!!! tip "Runtime estimates"
    A typical FEMM solve takes 2-10 seconds. A 176-configuration sweep takes approximately 10 minutes. Plan accordingly for larger parameter spaces.

- **Timeout per config**: set to 120s for simple geometries, 300s for complex ones
- **Failure handling**: always check `result.error` and skip failed configs gracefully
- **Progress reporting**: print progress inline with `flush=True` for notebook compatibility

---

## Visualization

The `heatsink_parametric.py` module includes several plotting functions:

| Function | Purpose |
|----------|---------|
| `plot_sensitivity(df, param)` | 1D line plot: R_th vs one parameter, others at nominal |
| `plot_heatmap(df, x, y)` | 2D heatmap: R_th over two parameters |
| `plot_scaling(df)` | Best R_th per base width |
| `plot_geometry_overlay(configs)` | Overlay cross-sections of multiple configs |
| `plot_contact_comparison(results)` | Compare contact alignment modes |

See [Heat Sink Parametric](../examples/heatsink-parametric.md) for a full walkthrough.
