# Heat Sink Tutorial (Baseline)

This example reproduces FEMM Tutorial #7: a 5-fin aluminum heat sink with a concentrated heat source. It validates py2femm against the known solution (T_avg approximately 356 K, R_th approximately 5.8 K/W).

**Source files:**

- Script: `examples/heatflow/heatsink/heatsink_tutorial.py`
- Notebook: `examples/heatflow/heatsink/heatsink_baseline.ipynb`
- Library: `examples/heatflow/heatsink/heatsink.py`

---

## Problem description

A 5-fin aluminum heat sink is cooled by natural convection. A 10W heat source is applied to a 4 mm contact patch centered on the bottom of the base.

### Dimensions

| Parameter | Value |
|-----------|-------|
| Base width | 35 mm |
| Base height | 5 mm |
| Fin width | 1.5 mm |
| Fin height | 20 mm |
| Number of fins | 5 |
| Fin gap | 7.375 mm |
| Extrusion depth | 100 mm |
| Contact width | 4 mm (centered) |

### Thermal parameters

| Parameter | Value |
|-----------|-------|
| Total power | 10 W |
| Contact area | 4 mm x 100 mm = 400 mm^2 |
| Heat flux (qs) | 25,000 W/m^2 |
| Convection coefficient (h) | 10 W/(m^2*K) |
| Ambient temperature (T_inf) | 298 K (25 C) |
| Aluminum conductivity (k) | 200 W/(m*K) |

---

## Step 1 -- Build the geometry

The heat sink cross-section is a single closed polygon tracing the full silhouette including all fin tips:

```python
from py2femm.geometry import Geometry, Node, Line

# Bottom edge with contact patch split points
nodes = [
    Node(0, 0),            # bottom-left
    Node(15.5, 0),         # contact start
    Node(19.5, 0),         # contact end
    Node(35, 0),           # bottom-right
    Node(35, 5),           # base top-right
]

# Zigzag over fins from right to left
for i in range(4, -1, -1):
    x_left = i * (1.5 + 7.375)
    x_right = x_left + 1.5
    nodes.extend([
        Node(x_right, 5),
        Node(x_right, 25),   # fin tip
        Node(x_left, 25),    # fin tip
        Node(x_left, 5),
    ])
```

After deduplication, this produces 24 unique nodes and 24 line segments forming the closed polygon.

!!! tip "Deduplication pattern"
    The fin zigzag generates duplicate nodes where fins meet the base. The standard deduplication removes consecutive nodes within 1e-6 tolerance. See [Geometry](../guide/geometry.md) for the full pattern.

---

## Step 2 -- Define materials and BCs

```python
from py2femm.heatflow import HeatFlowMaterial, HeatFlowHeatFlux, HeatFlowConvection

# Material
aluminum = HeatFlowMaterial(
    material_name="Aluminum", kx=200.0, ky=200.0, qv=0.0, kt=0.0
)
problem.add_material(aluminum)
problem.define_block_label(Node(17.5, 2.5), aluminum)

# Heat source on contact patch (nodes[1] -> nodes[2])
heat_source = HeatFlowHeatFlux(name="HeatSource", qs=-25000.0)
problem.add_boundary(heat_source)

# Convection on all other surfaces
convection = HeatFlowConvection(name="AirConvection", Tinf=298.0, h=10.0)
problem.add_boundary(convection)
```

### Boundary condition assignment

The critical logic for assigning BCs:

1. **Contact segment** (nodes[1] to nodes[2]) -- heat flux
2. **Bottom segments** (y=0, excluding contact) -- **left unassigned** (insulated)
3. **All other segments** -- convection

```python
# Assign heat flux to contact
contact_seg = Line(nodes[1], nodes[2])
problem.set_boundary_definition_segment(
    contact_seg.selection_point(), heat_source, elementsize=1
)

# Assign convection to all non-bottom, non-contact segments
for i in range(len(nodes)):
    if i == 1:
        continue  # skip contact segment
    seg = Line(nodes[i], nodes[(i + 1) % len(nodes)])
    if abs(seg.start_pt.y) < 1e-6 and abs(seg.end_pt.y) < 1e-6:
        continue  # bottom segment -- insulated
    problem.set_boundary_definition_segment(
        seg.selection_point(), convection, elementsize=1
    )
```

!!! warning "The BC bug fix"
    An earlier version of this example applied convection to **all** non-contact segments, including the bottom. This gave T_avg approximately 330 K instead of 356 K because the bottom was incorrectly cooled. The fix was to skip segments where both endpoints have y approximately 0 (the bottom edge). Bottom segments with no assigned BC default to insulated (zero flux), which is correct for a heat sink sitting on a PCB.

---

## Step 3 -- Solve and extract results

```python
problem.make_analysis("planar")

# Point temperatures
problem.lua_script.append("T_contact = ho_getpointvalues(17.5, 0)")
problem.lua_script.append("T_base = ho_getpointvalues(17.5, 2.5)")
problem.lua_script.append("T_fintip = ho_getpointvalues(0.75, 25)")

# Block integral: average temperature
problem.lua_script.append("ho_selectblock(17.5, 2.5)")
problem.lua_script.append("avg_T = ho_blockintegral(0)")
problem.lua_script.append("ho_clearblock()")

# Write to CSV
problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')
```

---

## Expected results

| Metric | Value |
|--------|-------|
| Average temperature (T_avg) | ~356 K (83 C) |
| Contact temperature (T_contact) | ~382 K |
| Fin tip temperature (T_fintip) | ~313 K |
| Thermal resistance (R_th) | ~5.8 K/W |

The thermal resistance is computed as:

```
R_th = (T_avg - T_ambient) / P = (356 - 298) / 10 = 5.8 K/W
```

---

## Running the example

### Script

```bash
# With server already running
python examples/heatflow/heatsink/heatsink_tutorial.py

# Auto-start server
python examples/heatflow/heatsink/heatsink_tutorial.py --start-server

# Skip plots (CI)
python examples/heatflow/heatsink/heatsink_tutorial.py --no-plot
```

### Notebook

```bash
jupyter notebook examples/heatflow/heatsink/heatsink_baseline.ipynb
```

The notebook version includes temperature contour bitmaps saved by FEMM's `ho_savebitmap()`.

---

## Next steps

- [Heat Sink Parametric](heatsink-parametric.md) -- vary fin geometry across 176 configurations
- [Chip Placement Optimization](optimization.md) -- optimize heat source placement
- [FemmProblem API](../guide/femm-problem.md) -- build your own problems
