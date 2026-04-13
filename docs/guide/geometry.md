# Geometry

The `py2femm.geometry` module provides primitives for 2D geometry construction: `Node`, `Line`, `CircleArc`, and `Geometry`. These are physics-independent -- the same geometry can be used for magnetic, thermal, or electrostatic problems.

---

## Node

A point in 2D space identified by `(x, y)` coordinates.

```python
from py2femm.geometry import Node

p = Node(10.0, 5.0)
print(p.x, p.y)  # 10.0 5.0
```

### Operations

Nodes support arithmetic and geometric transformations:

```python
a = Node(1, 2)
b = Node(3, 4)

c = a + b          # Node(4, 6)
d = a - b          # Node(-2, -2)
e = a * 2          # Node(2, 4)

dist = a.distance_to(b)   # 2.828...
rotated = a.rotate(3.14159 / 2)  # 90-degree CCW rotation
mirrored = a.mirror(0)    # mirror across y-axis -> Node(-1, 2)
```

Each node gets a unique UUID on creation. This ID is used internally to track nodes across geometry transformations (rotation, mirroring).

---

## Line

A line segment between two nodes:

```python
from py2femm.geometry import Line

seg = Line(start_pt=Node(0, 0), end_pt=Node(10, 0))
mid = seg.selection_point()  # Node(5, 0) -- midpoint
```

The `selection_point()` method returns the segment midpoint, which is used by FEMM to identify which segment to select when assigning boundary conditions.

---

## CircleArc

An arc defined by start point, center point, and end point:

```python
from py2femm.geometry import CircleArc

arc = CircleArc(
    start_pt=Node(10, 0),
    center_pt=Node(0, 0),
    end_pt=Node(0, 10),
)
```

FEMM calculates the arc angle from the start/end points and center. The `selection_point()` method returns a point on the arc midway between start and end.

---

## Geometry container

The `Geometry` class holds collections of nodes, lines, and arcs:

```python
from py2femm.geometry import Geometry, Node, Line

geo = Geometry()
geo.add_line(Line(Node(0, 0), Node(10, 0)))
geo.add_line(Line(Node(10, 0), Node(10, 5)))
geo.add_line(Line(Node(10, 5), Node(0, 5)))
geo.add_line(Line(Node(0, 5), Node(0, 0)))
```

### Node deduplication

When you add lines or arcs, `Geometry.append_node()` automatically deduplicates nodes within a tolerance of `1e-5`:

```python
geo = Geometry()
geo.add_line(Line(Node(0, 0), Node(10, 0)))
geo.add_line(Line(Node(10, 0), Node(10, 5)))  # Node(10,0) reused, not duplicated

print(len(geo.nodes))  # 3, not 4
```

!!! tip "Important for polygon construction"
    When building closed polygons from a node list, consecutive duplicate nodes (e.g., at fin base junctions) must be removed before creating lines. The standard pattern is:

    ```python
    nodes = [Node(0, 0), Node(5, 0), Node(5, 0), Node(10, 0)]  # duplicate!

    # Deduplicate consecutive nodes
    deduped = [nodes[0]]
    for n in nodes[1:]:
        if abs(n.x - deduped[-1].x) > 1e-6 or abs(n.y - deduped[-1].y) > 1e-6:
            deduped.append(n)
    # Remove last if same as first (closes the polygon)
    if (abs(deduped[-1].x - deduped[0].x) < 1e-6
            and abs(deduped[-1].y - deduped[0].y) < 1e-6):
        deduped.pop()
    ```

    This pattern is used throughout the heat sink examples.

---

## Building a closed polygon

The standard pattern for creating a closed polygon from ordered nodes:

```python
from py2femm.geometry import Geometry, Node, Line

# Define nodes in order (clockwise or counter-clockwise)
nodes = [
    Node(0, 0),
    Node(35, 0),
    Node(35, 5),
    Node(0, 5),
]

# Create geometry
geo = Geometry()
geo.nodes = list(nodes)

# Create line segments connecting consecutive nodes, closing the loop
lines = [Line(nodes[i], nodes[(i + 1) % len(nodes)]) for i in range(len(nodes))]
geo.lines = lines
```

!!! note
    Setting `geo.nodes` and `geo.lines` directly (as shown above) bypasses the deduplication in `add_line()`. This is fine when you've already deduplicated the node list manually.

---

## Geometry composition

Combine geometries using the `+` operator or `merge_geometry`:

```python
geo_base = Geometry()
# ... add base lines ...

geo_fins = Geometry()
# ... add fin lines ...

# Merge
combined = geo_base + geo_fins
# or
geo_base.merge_geometry(geo_fins)
```

Merging deduplicates nodes at shared boundaries automatically.

---

## DXF import

Import geometry from DXF files (requires `ezdxf`):

```python
geo = Geometry()
geo.import_dxf("my_model.dxf")
```

This reads `LINE` and `ARC` entities from the DXF modelspace. See `examples/SynRM/geom_from_dxf.py` for a real-world example.

---

## Transformations

Rotate an entire geometry around a point:

```python
geo.rotate_about(Node(0, 0), angle=45, degrees=True)
```

Mirror across an axis:

```python
geo.mirror(coord=0)  # mirror across y-axis (flip x)
geo.mirror(coord=1)  # mirror across x-axis (flip y)
```
