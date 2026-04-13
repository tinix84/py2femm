# Materials & Boundaries

Each FEMM physics type has its own material and boundary condition classes. This page covers all four supported fields.

---

## Heat Flow

### Material: `HeatFlowMaterial`

```python
from py2femm.heatflow import HeatFlowMaterial

aluminum = HeatFlowMaterial(
    material_name="Aluminum",
    kx=200.0,   # thermal conductivity in x-direction [W/(m*K)]
    ky=200.0,   # thermal conductivity in y-direction [W/(m*K)]
    qv=0.0,     # volumetric heat generation [W/m^3]
    kt=0.0,     # temperature coefficient of conductivity
)
```

### Boundary conditions

| Class | Type | Key Parameters |
|-------|------|----------------|
| `HeatFlowFixedTemperature` | Fixed T | `Tset` (K) |
| `HeatFlowHeatFlux` | Prescribed flux | `qs` (W/m^2) |
| `HeatFlowConvection` | Convection | `Tinf` (K), `h` (W/m^2/K) |
| `HeatFlowRadiation` | Radiation | `Tinf` (K), `beta` (emissivity) |
| `HeatFlowPeriodic` | Periodic | -- |
| `HeatFlowAntiPeriodic` | Anti-periodic | -- |

```python
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux

# Heat flux (negative = into the body)
heat_source = HeatFlowHeatFlux(name="HeatSource", qs=-25000.0)
heat_source.Tset = 0; heat_source.Tinf = 0; heat_source.h = 0; heat_source.beta = 0

# Convection
convection = HeatFlowConvection(name="AirConvection", Tinf=298.0, h=10.0)
convection.Tset = 0; convection.qs = 0; convection.beta = 0
```

!!! note "Heat flux sign convention"
    In FEMM, **negative** `qs` means heat flowing **into** the body. A 10W source over a 4mm x 100mm contact area gives `qs = -25000 W/m^2`.

!!! warning "The insulated-bottom gotcha"
    Segments with no assigned BC are treated as **insulated** (zero flux). For heat sinks mounted on a PCB, the bottom edge segments (except the heat source contact) should be left unassigned. If you accidentally apply convection to the bottom, the simulation over-predicts cooling and gives an unrealistically low thermal resistance.

---

## Magnetics

### Material: `MagneticMaterial`

```python
from py2femm.magnetics import MagneticMaterial, LamType

steel = MagneticMaterial(
    material_name="M19Steel",
    mu_x=1000.0,       # relative permeability x
    mu_y=1000.0,       # relative permeability y
    H_c=0.0,           # coercivity [A/m]
    J=0.0,             # source current density [MA/m^2]
    Sigma=0.0,         # electrical conductivity [MS/m]
    Lam_d=0.0,         # lamination thickness [mm]
    lam_fill=1.0,      # lamination fill factor
    LamType=LamType.NOT_LAMINATED,
)
```

For permanent magnets, set `H_c` and use `remanence_angle` on the material:

```python
magnet = MagneticMaterial(
    material_name="NdFeB",
    mu_x=1.05, mu_y=1.05,
    H_c=900000.0,
)
magnet.remanence_angle = 90  # magnetization direction in degrees
```

### BH curves

Add nonlinear BH data to a material:

```python
problem.add_bh_curve("M19Steel", data_b=[0, 0.5, 1.0, 1.5], data_h=[0, 50, 200, 5000])
```

Or use the `BHCurve` class for standalone BH data.

### Magnetic boundary conditions

Magnetic boundaries are defined using the general `Boundary` base class and configured through `add_boundary`. Common patterns include prescribed vector potential (A=0 for flux containment) and periodic boundaries for machine symmetry.

### Circuit properties

For winding analysis, define circuits:

```python
problem.add_circuit_property("WindingA", i=10.0, circuit_type=1)  # series
```

---

## Electrostatics

### Material: `ElectrostaticMaterial`

```python
from py2femm.electrostatics import ElectrostaticMaterial

dielectric = ElectrostaticMaterial(
    material_name="FR4",
    ex=4.5,    # relative permittivity x
    ey=4.5,    # relative permittivity y
    qv=0.0,    # volume charge density [C/m^3]
)
```

### Boundary conditions

| Class | Type | Key Parameters |
|-------|------|----------------|
| `ElectrostaticFixedVoltage` | Fixed V | `Vs` (V) |
| `ElectrostaticMixed` | Mixed | `c0`, `c1` |
| `ElectrostaticSurfaceCharge` | Surface charge | `qs` (C/m^2) |
| `ElectrostaticPeriodic` | Periodic | -- |
| `ElectrostaticAntiPeriodic` | Anti-periodic | -- |

```python
from py2femm.electrostatics import ElectrostaticFixedVoltage

gnd = ElectrostaticFixedVoltage(name="Ground", Vs=0.0)
hv = ElectrostaticFixedVoltage(name="HighVoltage", Vs=100.0)
```

---

## Current Flow

### Material: `CurrentFlowMaterial`

```python
from py2femm.current_flow import CurrentFlowMaterial

copper = CurrentFlowMaterial(
    material_name="Copper",
    ox=58.0,    # conductivity x [MS/m]
    oy=58.0,    # conductivity y [MS/m]
    ex=1.0,     # relative permittivity x
    ey=1.0,     # relative permittivity y
    ltx=0.0,    # dielectric loss tangent x
    lty=0.0,    # dielectric loss tangent y
)
```

### Boundary conditions

| Class | Type | Key Parameters |
|-------|------|----------------|
| `CurrentFlowFixedVoltage` | Fixed V | `Vs` (V) |
| `CurrentFlowMixed` | Mixed | `c0`, `c1` |
| `CurrentFlowSurfaceCurrent` | Surface current | `qs` (A/m) |
| `CurrentFlowPeriodic` | Periodic | -- |
| `CurrentFlowAntiPeriodic` | Anti-periodic | -- |

---

## Assigning BCs to segments

The pattern is the same for all physics types:

```python
# 1. Add the boundary definition
problem.add_boundary(my_boundary)

# 2. Find the segment midpoint
seg = Line(node_a, node_b)
midpoint = seg.selection_point()

# 3. Assign BC to the segment nearest the midpoint
problem.set_boundary_definition_segment(midpoint, my_boundary, elementsize=1)
```

For arc segments, use `set_boundary_definition_arc`:

```python
arc = CircleArc(start, center, end)
problem.set_boundary_definition_arc(arc.selection_point(), my_boundary, maxsegdeg=5)
```

!!! tip
    The `selection_point()` method on `Line` returns the midpoint. FEMM selects the segment closest to this point, so make sure no two segments share the same midpoint. For complex geometries, iterate over all segments and use the midpoint coordinates to decide which BC to apply.
