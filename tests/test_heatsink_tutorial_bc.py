"""Regression test: bottom segments at y=0 must NOT get convection BC."""

from heatsink_tutorial import build_outline_nodes, build_geometry, build_femm_problem, get_lua_script


def test_bottom_segments_not_convection():
    """Segments at y=0 (other than contact) must be insulated (no BC)."""
    nodes = build_outline_nodes()
    geo, lines = build_geometry(nodes)
    problem = build_femm_problem(nodes, geo)
    lua = get_lua_script(problem)

    # Count how many times hi_selectsegment is called at y=0.0
    # Only the contact patch midpoint (y=0) should appear
    select_calls = [line for line in lua.splitlines() if "hi_selectsegment" in line]
    y0_selects = []
    for call in select_calls:
        # Parse: hi_selectsegment(x, y)
        inner = call.split("(")[1].split(")")[0]
        parts = inner.split(",")
        y_val = float(parts[1].strip())
        if abs(y_val) < 1e-6:
            y0_selects.append(call)

    # Only ONE segment at y=0 should be selected: the contact patch
    assert len(y0_selects) == 1, (
        f"Expected 1 segment selection at y=0 (contact only), got {len(y0_selects)}:\n"
        + "\n".join(y0_selects)
    )
