# FemmProblem API

`FemmProblem` is the central class in py2femm. It builds a Lua script that FEMM can execute to create a model, mesh it, solve, and extract results.

---

## Construction

```python
from py2femm.femm_problem import FemmProblem

problem = FemmProblem(out_file="results.csv")
```

The `out_file` parameter sets the CSV filename where FEMM writes results. This file is created inside the FEMM working directory and returned via the server.

---

## Problem definition

Call one of the four problem-type methods to set the physics and initialize the Lua script:

### Heat flow

```python
from py2femm.general import LengthUnit

problem.heat_problem(
    units=LengthUnit.MILLIMETERS,
    type="planar",       # or "axi" for axisymmetric
    precision=1e-8,
    depth=100,           # extrusion depth [mm] for planar problems
    minangle=30,         # mesh quality constraint
)
```

### Magnetics

```python
problem.magnetic_problem(
    freq=0,              # 0 for magnetostatic
    unit=LengthUnit.MILLIMETERS,
    type="planar",
    precision=1e-8,
    depth=1,
    minangle=30,
    acsolver=0,          # 0 = successive approximation, 1 = Newton
)
```

### Electrostatics

```python
problem.electrostatic_problem(
    units=LengthUnit.MILLIMETERS,
    type="planar",
    precision=1e-8,
    depth=1,
    minangle=30,
)
```

### Current flow

```python
problem.currentflow_problem(
    units=LengthUnit.MILLIMETERS,
    type="planar",
    frequency=0,         # 0 for DC
    precision=1e-8,
    depth=1,
    minangle=30,
)
```

!!! note
    You must call exactly one of these methods before adding geometry, materials, or boundaries. The method sets the `field` attribute, which determines the Lua command prefix (`hi_`, `mi_`, `ei_`, or `ci_`).

---

## Geometry

Pass a `Geometry` object containing nodes and line segments:

```python
from py2femm.geometry import Geometry, Node, Line

geo = Geometry()
geo.nodes = [Node(0, 0), Node(10, 0), Node(10, 5), Node(0, 5)]
geo.lines = [
    Line(geo.nodes[0], geo.nodes[1]),
    Line(geo.nodes[1], geo.nodes[2]),
    Line(geo.nodes[2], geo.nodes[3]),
    Line(geo.nodes[3], geo.nodes[0]),
]

problem.create_geometry(geo)
```

See [Geometry](geometry.md) for details on node deduplication and polygon construction.

---

## Materials

Add a material definition, then assign it to a region via a block label:

```python
from py2femm.heatflow import HeatFlowMaterial

aluminum = HeatFlowMaterial(
    material_name="Aluminum",
    kx=200.0,   # thermal conductivity x [W/(m*K)]
    ky=200.0,   # thermal conductivity y
    qv=0.0,     # volume heat generation [W/m^3]
    kt=0.0,     # temperature coefficient
)
problem.add_material(aluminum)
```

See [Materials & Boundaries](materials-boundaries.md) for all physics types.

---

## Block labels

A block label tells FEMM which material occupies a region. Place it inside the closed polygon:

```python
label = Node(5, 2.5)  # inside the rectangle
problem.define_block_label(label, aluminum)
```

`define_block_label` is a convenience method that calls `add_blocklabel`, `select_label`, `set_blockprop`, and `clear_selected` in sequence.

---

## Boundary conditions

Add boundary definitions and assign them to segments:

```python
from py2femm.heatflow import HeatFlowHeatFlux, HeatFlowConvection

# Define BCs
heat_source = HeatFlowHeatFlux(name="HeatSource", qs=-25000.0)
heat_source.Tset = 0; heat_source.Tinf = 0; heat_source.h = 0; heat_source.beta = 0
problem.add_boundary(heat_source)

convection = HeatFlowConvection(name="AirConvection", Tinf=298.0, h=10.0)
convection.Tset = 0; convection.qs = 0; convection.beta = 0
problem.add_boundary(convection)
```

### Assigning BCs to segments

Use `set_boundary_definition_segment` with a point near the segment midpoint:

```python
# Assign heat flux to the contact segment
contact_seg = Line(nodes[1], nodes[2])
problem.set_boundary_definition_segment(
    contact_seg.selection_point(),  # midpoint of the segment
    heat_source,
    elementsize=1,
)
```

!!! warning "Insulated segments"
    Segments without an assigned BC are treated as insulated (zero flux) by FEMM. This is the correct default for bottom edges of heat sinks that sit on a PCB. If you accidentally assign convection to the bottom, your thermal resistance will be too low.

---

## Analysis

`make_analysis` saves the model, runs the solver, and loads the solution for post-processing:

```python
problem.make_analysis("planar")
```

This generates three Lua commands: `hi_saveas(...)`, `hi_analyze(0)`, `hi_loadsolution()`.

---

## Post-processing with raw Lua

For operations not yet wrapped by py2femm (e.g., heat flow block integrals), append raw Lua commands:

```python
# Select block and compute average temperature
problem.lua_script.append(f"ho_selectblock({x}, {y})")
problem.lua_script.append("avg_T = ho_blockintegral(0)")
problem.lua_script.append("ho_clearblock()")

# Write result to CSV
problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')
```

The `file_out` handle is opened automatically by `init_problem` and closed by `close`.

---

## Writing and closing

### Generate Lua script as a string

```python
problem.close()       # append close commands (flush files, quit FEMM)
lua_script = "\n".join(problem.lua_script)
```

### Write to file

```python
problem.write("my_simulation.lua")  # calls close() automatically
```

!!! note
    `close()` appends a `PY2FEMM_DONE` sentinel to the output file. The server executor watches for this marker to know the simulation completed. Do not call `close()` twice -- it will duplicate the quit commands.

---

## Complete example

```python
from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Node, Line
from py2femm.heatflow import HeatFlowMaterial, HeatFlowConvection, HeatFlowHeatFlux
from py2femm.client import FemmClient

# 1. Build problem
problem = FemmProblem(out_file="results.csv")
problem.heat_problem(units=LengthUnit.MILLIMETERS, type="planar",
                     precision=1e-8, depth=100, minangle=30)

# 2. Geometry (simple rectangle)
geo = Geometry()
nodes = [Node(0, 0), Node(10, 0), Node(10, 5), Node(0, 5)]
geo.nodes = nodes
geo.lines = [Line(nodes[i], nodes[(i+1) % 4]) for i in range(4)]
problem.create_geometry(geo)

# 3. Material
alu = HeatFlowMaterial(material_name="Aluminum", kx=200, ky=200, qv=0, kt=0)
problem.add_material(alu)
problem.define_block_label(Node(5, 2.5), alu)

# 4. Boundary conditions
flux = HeatFlowHeatFlux(name="Source", qs=-10000)
flux.Tset = 0; flux.Tinf = 0; flux.h = 0; flux.beta = 0
problem.add_boundary(flux)

conv = HeatFlowConvection(name="Cooling", Tinf=298, h=10)
conv.Tset = 0; conv.qs = 0; conv.beta = 0
problem.add_boundary(conv)

# Assign BCs
bottom = Line(nodes[0], nodes[1])
problem.set_boundary_definition_segment(bottom.selection_point(), flux, elementsize=1)
for i in [1, 2, 3]:
    seg = Line(nodes[i], nodes[(i+1) % 4])
    problem.set_boundary_definition_segment(seg.selection_point(), conv, elementsize=1)

# 5. Solve
problem.make_analysis("planar")
problem.lua_script.append(f"ho_selectblock(5, 2.5)")
problem.lua_script.append("avg_T = ho_blockintegral(0)")
problem.lua_script.append("ho_clearblock()")
problem.lua_script.append('write(file_out, "T_avg = ", avg_T, "\\n")')

# 6. Execute
problem.close()
lua = "\n".join(problem.lua_script)

client = FemmClient(mode="remote", url="http://localhost:8082")
result = client.run(lua, timeout=120)
print(result.csv_data)
```
