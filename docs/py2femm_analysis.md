# py2femm Source Code Analysis

**Date:** 2026-04-05  
**Scope:** Detailed analysis of py2femm GitHub repository structure, class definitions, method signatures, and Lua generation patterns.  
**Purpose:** Support refactoring effort to create MATLAB/Octave equivalent (`femm_generator.m`)

---

## 1. Package Configuration & Entry Points

**File:** `pyproject.toml`

- **Package:** `py2femm`
- **Version:** `0.1.0`
- **Python requirement:** `^3.10` (Python 3.10+)
- **Dependencies:** `aio-pika` (async RabbitMQ client)
- **Dev dependencies:** `pytest ^5.2`
- **Build tool:** Poetry
- **Entry points:** None (library-only, no CLI)

---

## 2. Module Hierarchy & Imports

**File:** `py2femm/__init__.py`

- Exports `__version__ = '0.1.0'`
- No public API exports documented (minimal init file)

**Import chain pattern:**
```python
# Typical usage:
from py2femm.femm_problem import FemmProblem
from py2femm.geometry import Node, Line, CircleArc, Sector, Geometry
from py2femm.heatflow import HeatFlowMaterial, HeatFlowFixedTemperature, etc.
from py2femm.general import Material, Boundary, AutoMeshOption, FemmFields, LengthUnit
from py2femm.executor import Executor, RabbitExecutor
```

---

## 3. Core Geometry Classes (`py2femm/geometry.py`)

### 3.1 Node Class

**No decorators** — regular class

```python
class Node:
    def __init__(self, x=0.0, y=0.0, id=None, label=None, precision=6):
        # x, y: float coordinates
        # id: optional unique identifier
        # label: optional string label
        # precision: decimal places for rounding (default 6)
```

**Key methods:**
- `__add__(p: Node) -> Node` — Returns new Node with summed coordinates
- `__sub__(p: Node) -> Node` — Returns new Node with subtracted coordinates
- `__mul__(scalar: float) -> Node` — Returns scaled Node
- `length() -> float` — Euclidean norm sqrt(x² + y²)
- `distance_to(p: Node) -> float` — Distance between two nodes
- `as_tuple() -> (float, float)` — Returns (x, y) tuple
- `clone() -> Node` — Deep copy preserving ID
- `move_xy(dx: float, dy: float)` — In-place translation with rounding
- `rotate(rad: float, degrees=False) -> Node` — Rotates around origin
- `rotate_about(p: Node, theta: float, degrees=False) -> Node` — Rotates around pivot
- `mirror(coord: int=0) -> Node` — Mirrors across x-axis (0) or y-axis (1)

### 3.2 Line Class

**Decorated:** `@dataclass`

```python
@dataclass
class Line:
    id = uuid.uuid4()  # Class-level default
    start_pt: Node
    end_pt: Node
```

**Key methods:**
- `selection_point() -> Node` — Returns midpoint
- `distance_to_point(px: float, py: float) -> float` — Minimum distance using projection

### 3.3 CircleArc Class

**Decorated:** `@dataclass`

```python
@dataclass
class CircleArc:
    start_pt: Node
    center_pt: Node
    end_pt: Node
    id = uuid.uuid4()  # Class-level default
```

**Key methods:**
- `selection_point() -> Node` — Returns point on arc at mid-angle
- (Angle computed from start/center/end geometry)

### 3.4 Sector Class

**Decorated:** `@dataclass`

```python
@dataclass
class Sector:
    start_pt: Node
    end_pt: Node
    degree: float  # Arc angle in degrees
    id = uuid.uuid4()  # Class-level default
```

**Key methods:**
- `convert() -> CircleArc` — Transforms to CircleArc
- `selection_point() -> Node` — Calculates center then returns mid-angle point
- `center_point() -> Node` — Returns calculated arc center
- `mid_point() -> Node` — Returns chord midpoint

### 3.5 CubicBezier Class

(Not detailed in WebFetch, but referenced in Geometry.cubic_beziers list)

### 3.6 Geometry Class

**No decorators** — container class

```python
class Geometry:
    def __init__(self):
        self.nodes = []          # list[Node]
        self.lines = []          # list[Line]
        self.circle_arcs = []    # list[CircleArc]
        self.cubic_beziers = []  # list[CubicBezier]
        self.precision = 1e-5    # Class attribute
```

**Key methods:**
- `__add__(g: Geometry) -> Geometry` — Concatenates nodes, lines, arcs from both
- `duplicate() -> Geometry` — Deep copy with independent elements
- `update_nodes(node: Node)` — Synchronizes node references in lines/arcs/beziers
- `rotate_about(node: Node, angle: float, degrees: bool)` — Rotates all elements
- `append_node(new_node: Node)` — Adds node (duplicate check within precision)
- `add_node(node: Node)` — Wrapper for append_node
- `add_line(line: Line)` — Adds line, ensures endpoints registered
- `add_arc(arc: CircleArc)` — Adds arc, ensures endpoints registered
- `add_sector(sector: Sector)` — Converts to CircleArc then adds
- `add_cubic_bezier(cb: CubicBezier)` — Adds bezier, ensures endpoints registered
- `delete_hanging_nodes()` — Removes unreferenced nodes
- `merge_geometry(other: Geometry)` — Merges other Geometry's elements
- `merge_lines()` — Removes duplicate lines
- `meshi_it(mesh_strategy)` — Mesh generation
- `delete_line(x: float, y: float)` — Delete line closest to (x,y)
- `find_node(id)` — Retrieve node by ID
- `import_dxf(dxf_file: str)` — Import from DXF
- `mirror(coord: int)` — Mirror across x (0) or y (1)
- `@staticmethod approx_circle(circle)` — Approximate arc as segments
- `@staticmethod casteljau(bezier)` — De Casteljau iteration

---

## 4. Thermal Analysis Classes (`py2femm/heatflow.py`)

### 4.1 HeatFlowMaterial

**Decorated:** `@dataclass`  
**Inherits:** `Material`

```python
@dataclass
class HeatFlowMaterial(Material):
    kx: float         # Thermal conductivity, x-direction
    ky: float         # Thermal conductivity, y-direction
    qv: float         # Volumetric heat generation
    kt: float         # Transient thermal parameter
```

**Lua generation template:**
```
hi_addmaterial($materialname, $kx, $ky, $qv, $kt)
```

### 4.2 HeatFlowBaseClass

**Decorated:** `@dataclass`  
**Inherits:** `Boundary`

```python
@dataclass
class HeatFlowBaseClass(Boundary):
    type: int              # Boundary condition identifier
    Tset: float = 0        # Set temperature
    qs: float = 0          # Heat flux
    Tinf: float = 0        # Ambient temperature
    h: float = 0           # Convection coefficient
    beta: float = 0        # Radiation emissivity
```

### 4.3 Boundary Condition Subclasses

All inherit from `HeatFlowBaseClass`:

| Class | Type | Constructor | Purpose |
|-------|------|-------------|---------|
| `HeatFlowFixedTemperature` | 0 | `(name, Tset)` | Constant temperature |
| `HeatFlowHeatFlux` | 1 | `(name, qs)` | Specified heat flux |
| `HeatFlowConvection` | 2 | `(name, Tinf, h)` | Convection BC |
| `HeatFlowRadiation` | 3 | `(name, Tinf, beta)` | Radiation BC |
| `HeatFlowPeriodic` | 4 | `(name)` | Periodic symmetry |
| `HeatFlowAntiPeriodic` | 5 | `(name)` | Anti-periodic |

Each subclass sets `type` field and initializes relevant thermal parameters.

---

## 5. Base Classes (`py2femm/general.py`)

### 5.1 Imports & Decorators

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional
```

### 5.2 Material Base Class

**Decorated:** `@dataclass`  
**Abstract:** Yes (ABC)

```python
@dataclass
class Material(ABC):
    material_name: str
    auto_mesh: AutoMeshOption      # Enum for mesh strategy
    mesh_size: float
    b: Optional[...] = None        # BH curve points (magnetic context)
    h: Optional[...] = None        # BH curve points (magnetic context)
    material_positions: Optional[list] = None
    remanence_angle: Optional[float] = None
```

### 5.3 Boundary Base Class

**Decorated:** `@dataclass`  
**Abstract:** Yes (ABC)

```python
@dataclass
class Boundary(ABC):
    name: str
    type: int
    boundary_edges: Optional[list] = None
```

### 5.4 Enums

```python
class AutoMeshOption(Enum):
    # Mesh strategy options
    ...

class FemmFields(Enum):
    # Field types with conversion methods
    MAGNETIC = "mi"  # Magnetic
    THERMAL = "hi"   # Heat flow (hi_*)
    ELECTROSTATIC = "ei"
    CURRENTFLOW = "ci"
    
    def input_to_string(self) -> str:
        # "magnetic" → "mi"
    
    def output_to_string(self) -> str:
        # "magnetic" → "mo"

class LengthUnit(Enum):
    # meter, centimeter, millimeter, etc.
    ...
```

---

## 6. Main Solver Class (`py2femm/femm_problem.py`)

### 6.1 FemmProblem Class

**No inheritance** — standalone class

```python
class FemmProblem:
    def __init__(self, out_file="fem_data.csv"):
        self.field = None                    # FemmFields enum value
        self.lua_script = []                 # list[str] — accumulated Lua commands
        self.out_file = out_file
        self.integral_counter = 0
        self.mesh_file = "elements.csv"
        self.node_file = "node.csv"
        self.node_nr = "node_nr"
        self.element_nr = "element_nr"
        self.point_values = "point_values.csv"
        self.nodal_coords = []
        self.element_coords = []
        self.post_processing_activated = False
```

### 6.2 Problem Definition Methods

All append to `self.lua_script` list. Use `${field}` template variable for field prefix (mi_, hi_, ei_, ci_).

```python
def magnetic_problem(freq: float, unit: str, type: str, 
                     precision: float, depth: float, 
                     minangle: float, acsolver: int):
    # Template: mi_probdef($frequency,$units,$type,$precision, $depth, $minangle, $acsolver)

def heat_problem(units: str, type: str, precision: float, 
                 depth: float, minangle: float, 
                 prevsoln: int = 0, timestep: float = 0):
    # F-string template: hi_probdef(...)

def electrostatic_problem(units: str, type: str, precision: float, 
                          depth: float, minangle: float):
    # F-string template: ei_probdef(...)

def currentflow_problem(units: str, type: str, frequency: float, 
                        precision: float, depth: float, minangle: float):
    # F-string template: ci_probdef(...)
```

### 6.3 Geometry Operations

```python
def create_geometry(geometry: Geometry):
    # Processes all nodes, lines, arcs from Geometry object

def add_node(node: Node):
    # Template: "${field}_addnode($x_coord, $y_coord)"

def add_segment(start_pt: Node, end_pt: Node):
    # Template: "${field}_addsegment($x1_coord, $y1_coord, $x2_coord, $y2_coord)"

def add_arc(start_pt: Node, end_pt: Node, angle: float, maxseg: float):
    # Template: "${field}_addarc($x_1, $y_1, $x_2, $y_2, $angle, $maxseg)"

def add_blocklabel(label: Node):
    # Template: "${field}_addblocklabel($x_coord, $y_coord)"
```

### 6.4 Material & Property Operations

```python
def add_material(material: Material):
    # Appends material string, optionally adds BH curve points

def add_bh_curve(material_name: str, data_b: list, data_h: list):
    # Template: 'mi_addbhpoint("$material_name", $bi, $hi)' for each point

def add_boundary(boundary: Boundary):
    # Converts boundary object to Lua string

def add_point_property(prop_name: str, **kwargs):
    # Field-specific templates for electrostatics, magnetics, heat flow, current flow

def add_circuit_property(circuit_name: str, i: float, circuit_type: int):
    # Template: 'mi_addcircprop("$circuit_name",$i,$circuit_type)'
```

### 6.5 Block & Segment Properties

```python
def set_blockprop(blockname: str, automesh: bool, meshsize: float, 
                  group: int, **kwargs):
    # Template varies by field (mi_setblockprop, hi_setblockprop, etc.)

def set_segment_prop(propname: str, elementsize: float, automesh: bool, 
                     hide: bool, group: int, inductor: bool):
    # Template: "${field}_setsegmentprop(...)"

def set_arc_segment_prop(maxsegdeg: float, propname: str, 
                         hide: bool, group: int):
    # Field-specific (magnetic, electrostatic)
```

### 6.6 Analysis & Post-Processing

```python
def analyze(flag: int = 0):
    # Template: "${field}_analyze($flag)"

def load_solution():
    # Template: "${field}_loadsolution()"

def save_as(file_name: str):
    # Template: "${field}_saveas($filename)"

def get_point_values(point: Node) -> dict:
    # Retrieves field values at point
    # Possible keys: A, B1, B2, Sig, E, H1, H2, Je, Js, Mu1, Mu2, Pe, Ph

def block_integral(type: int) -> float:
    # Calculates block integral (type 0-30 options available)

def line_integral(type: int) -> float:
    # Calculates line contour integral
```

### 6.7 Selection Operations

```python
def select_node(node: Node)
def select_segment(x: float, y: float)
def select_arc_segment(x: float, y: float)
def select_label(label: Node)
def select_circle(x: float, y: float, R: float, editmode: bool)
def select_rectangle(x1: float, y1: float, x2: float, y2: float, editmode: bool)
def select_group(n: int)
```

### 6.8 Deletion Operations

```python
def delete_selected()
def delete_selected_nodes()
def delete_selected_labels()
def delete_selected_segments()
def delete_selected_arc_segments()
def clear_selected()
```

### 6.9 Lua Script Output

```python
def write(file_name: str, close_after: bool = True):
    # Outputs accumulated self.lua_script list as newline-separated commands
    # Lua file ready for FEMM interpreter
```

---

## 7. Executor Classes (`py2femm/executor.py`)

### 7.1 Executor Class

```python
class Executor:
    # Platform detection: Linux uses Wine (~/.wine/drive_c/femm42/bin/femm.exe)
    #                     Windows uses direct path (C:\femm42\bin\femm.exe)
    
    def run(script_file: str, timeout: int = 1000):
        # Executes FEMM with Lua script via subprocess
        # Arguments: "-lua-script={script_file}"
        # Uses Timer for timeout management
        # Subprocess pattern: Popen with stdout/stderr piping
```

### 7.2 RabbitExecutor Class

```python
class RabbitExecutor:
    def __init__(self, name: str = "py2femm-rabbitmq", script_files: list = []):
        self.name = name
        self.script_files = script_files
        self.executor = Executor()
        # Initializes Registry for RabbitMQ
    
    async def worker(self, max_workers: int = 4):
        # Uses ProcessPoolExecutor with max 4 workers
    
    async def broker(self):
        # Uses NullExecutor for RabbitMQ distributed tasks (AMQP protocol)
```

---

## 8. Lua Generation Patterns

### 8.1 String Template Strategy

**Used in:** `add_node()`, `add_segment()`, `add_arc()`, etc.

```python
from string import Template

# Example:
template = Template("${field}_addnode($x_coord, $y_coord)")
lua_command = template.substitute(field="hi", x_coord=0.5, y_coord=1.0)
# Result: "hi_addnode(0.5, 1.0)"
```

### 8.2 F-String Strategy

**Used in:** `heat_problem()`, `electrostatic_problem()`, etc.

```python
# Example:
units = "meters"
type_str = "axi"
lua_command = f"hi_probdef('{units}', '{type_str}', ...)"
```

### 8.3 Lua Command Accumulation

All geometry/material/property operations **append strings to `self.lua_script` list**:

```python
def add_node(self, node: Node):
    template = Template("${field}_addnode($x_coord, $y_coord)")
    cmd = template.substitute(field=self.field.input_to_string(), 
                              x_coord=node.x, 
                              y_coord=node.y)
    self.lua_script.append(cmd)  # <-- Key pattern
```

### 8.4 Write-to-File Pattern

```python
def write(self, file_name: str, close_after: bool = True):
    with open(file_name, 'w') as f:
        # Write all accumulated commands, one per line
        for cmd in self.lua_script:
            f.write(cmd + '\n')
        # Optionally close FEMM
        if close_after:
            f.write("femm.closefemm()\n")
```

---

## 9. Key Design Patterns

### 9.1 Separation of Concerns

- **Geometry:** Independent of field type (Geometry can be reused)
- **Field definition:** Separate method for each physics type (magnetic, thermal, etc.)
- **Lua generation:** Centralized in FemmProblem class

### 9.2 Container Pattern

- `Geometry` acts as container for nodes, lines, arcs
- `FemmProblem` acts as container for Lua commands
- Both accumulate objects/commands, then serialize

### 9.3 Dataclass + Inheritance

```python
@dataclass
class HeatFlowMaterial(Material):
    kx: float
    ky: float
    # ...inherits material_name, auto_mesh, mesh_size from Material
```

### 9.4 Template Substitution for Lua

Uses `string.Template` with `${field}` placeholder to inject field prefix dynamically:
- `mi_` for magnetic
- `hi_` for heat flow
- `ei_` for electrostatic
- `ci_` for current flow

### 9.5 Optional Parameters via **kwargs

```python
def add_point_property(self, prop_name: str, **kwargs):
    # Handles field-specific parameters without explicit method overloading
```

---

## 10. Critical Implementation Notes

1. **No ActiveX:** py2femm avoids ActiveX entirely — it generates text Lua files only.

2. **File-based interface:** All interactions are through generated `.lua` scripts, not live API calls.

3. **Lua output is human-readable:** Each command is a plain Lua line, can be inspected/debugged.

4. **Precision handling:** Node class supports configurable decimal precision (default 6).

5. **Geometry validation:** `append_node()` uses `precision` threshold to detect duplicates.

6. **Enum-based field selection:** `FemmFields.THERMAL.input_to_string()` returns `"hi"` for template substitution.

7. **Async execution optional:** `RabbitExecutor` allows distributed FEMM runs via RabbitMQ (advanced feature).

8. **Transient thermal support:** `heat_problem()` accepts `prevsoln` (previous solution) and `timestep` for time-stepping.

---

## 11. MATLAB/Octave Refactoring Implications

### Feasible Direct Translations

- ✓ Node class (struct with methods → classdef)
- ✓ Geometry container (cell arrays of objects)
- ✓ Material definitions (struct dataclasses → classdef)
- ✓ FemmProblem central dispatcher (main class)
- ✓ Lua generation via string concatenation (sprintf/strcat)
- ✓ File I/O (fopen/fprintf)

### Requires Adaptation

- Dataclass decorators → classdef with properties
- abc.ABC abstractmethod → Octave abstract pattern (if needed)
- enum.Enum → classdef with constant properties
- uuid.uuid4() → alternative unique ID scheme
- string.Template → sprintf with %s placeholders
- subprocess.Popen → system() calls (Octave-specific)

### Recommended Octave Patterns

1. **Struct-based nodes:** Use struct arrays for simplicity
   ```octave
   node.x = 0.5;
   node.y = 1.0;
   ```

2. **Cell arrays for geometry:** Store nodes/lines/arcs in cell arrays
   ```octave
   geometry.nodes = {};
   geometry.lines = {};
   ```

3. **sprintf for Lua:** Build commands dynamically
   ```octave
   cmd = sprintf('hi_addnode(%g, %g)', node.x, node.y);
   lua_script{end+1} = cmd;
   ```

4. **File export:** Use fprintf() in loop
   ```octave
   fid = fopen('script.lua', 'w');
   for i = 1:length(lua_script)
       fprintf(fid, '%s\n', lua_script{i});
   end
   fclose(fid);
   ```

---

## 12. Testing & Validation

The analysis reveals py2femm does **not include unit tests** for Lua generation (only pytest configuration for integration tests). 

For Octave port:
- Generate sample Lua scripts
- Verify output matches py2femm reference
- Test with actual FEMM to ensure correctness

---

## References

- GitHub: https://raw.githubusercontent.com/tamasorosz/py2femm/master/
- Key modules:
  - `py2femm/femm_problem.py` (46 KB) — FemmProblem dispatcher
  - `py2femm/geometry.py` — Node, Line, CircleArc, Geometry
  - `py2femm/heatflow.py` — HeatFlowMaterial, boundary conditions
  - `py2femm/general.py` — Base Material, Boundary, enums
  - `py2femm/executor.py` — FEMM subprocess runner

