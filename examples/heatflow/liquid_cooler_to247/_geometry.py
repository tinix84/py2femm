from __future__ import annotations

from py2femm.geometry import Geometry, Line, Node


def add_rect(geo: Geometry, x0: float, y0: float, x1: float, y1: float) -> None:
    """Add four Line segments forming a closed rectangle to geo."""
    bl, br, tr, tl = Node(x0, y0), Node(x1, y0), Node(x1, y1), Node(x0, y1)
    geo.add_line(Line(bl, br))
    geo.add_line(Line(br, tr))
    geo.add_line(Line(tr, tl))
    geo.add_line(Line(tl, bl))
