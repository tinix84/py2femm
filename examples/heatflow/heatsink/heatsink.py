"""Heat Sink Thermal Analysis with py2femm.

Translated from the FEMM heat flow tutorial video:
https://www.youtube.com/watch?v=1I1mQAT1Kts

Problem:
    Aluminum heat sink with 5 fins, 100mm deep.
    10W heat source on 4mm contact area on bottom of base.
    Convective cooling: h=10 W/(m^2*K), T_ambient=298K (25C).

    Expected: T_heatsink ~ 356K (83C), R_th ~ 5.8 K/W
"""

import argparse
from pathlib import Path

from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Node, Line
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial


def build_heatsink_problem() -> FemmProblem:
    """Build heat sink geometry and return FemmProblem.

    Cross-section (mm):
        5 fins: 1.5mm wide, 20mm tall
        Base: 35mm wide, 5mm tall
        Contact: 4mm centered on bottom

              fin0  fin1  fin2  fin3  fin4
              |  |  |  |  |  |  |  |  |  |
              |  |  |  |  |  |  |  |  |  |  20mm
              |  |  |  |  |  |  |  |  |  |
              +--+--+--+--+--+--+--+--+--+
              |         BASE              |  5mm
              +------+====+---------------+
                     4mm heat source
              |<--------- 35mm ---------->|
    """
    problem = FemmProblem(out_file="heatsink_data.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS,
        type="planar",
        precision=1e-8,
        depth=100,
        minangle=30,
    )

    geo = Geometry()

    # Dimensions
    base_w = 35.0
    base_h = 5.0
    fin_w = 1.5
    fin_h = 20.0
    n_fins = 5
    gap = (base_w - n_fins * fin_w) / (n_fins - 1)  # gap between fins

    contact_w = 4.0
    cx0 = (base_w - contact_w) / 2.0  # 15.5
    cx1 = cx0 + contact_w              # 19.5

    # Build outline as ordered nodes, clockwise from bottom-left.
    # The heat sink is one closed polygon tracing the full silhouette.
    #
    # Bottom: (0,0) -> (cx0,0) -> (cx1,0) -> (W,0)
    # Right:  (W,0) -> (W,H)
    # Top:    zigzag right-to-left over each fin
    # Left:   (0,H) -> (0,0)
    nodes = [
        Node(0, 0),        # bottom-left
        Node(cx0, 0),      # contact start
        Node(cx1, 0),      # contact end
        Node(base_w, 0),   # bottom-right
        Node(base_w, base_h),  # base top-right
    ]

    # Zigzag over fins from right to left
    for i in range(n_fins - 1, -1, -1):
        x_left = i * (fin_w + gap)
        x_right = x_left + fin_w

        # Fin base-right (at base_h level) — skip if same as previous node
        nodes.append(Node(x_right, base_h))
        # Fin tip-right
        nodes.append(Node(x_right, base_h + fin_h))
        # Fin tip-left
        nodes.append(Node(x_left, base_h + fin_h))
        # Fin base-left
        nodes.append(Node(x_left, base_h))

    # Close: last node is (0, base_h), connect back to (0, 0)

    # Deduplicate consecutive nodes at same coordinates
    deduped = [nodes[0]]
    for n in nodes[1:]:
        if abs(n.x - deduped[-1].x) > 1e-6 or abs(n.y - deduped[-1].y) > 1e-6:
            deduped.append(n)
    # Also check last->first
    if abs(deduped[-1].x - deduped[0].x) < 1e-6 and abs(deduped[-1].y - deduped[0].y) < 1e-6:
        deduped.pop()
    nodes = deduped

    # Close the outline: connect last node back to first
    # All nodes in order form a closed polygon
    geo.nodes = list(nodes)

    # Create line segments connecting consecutive nodes
    lines = []
    for i in range(len(nodes) - 1):
        lines.append(Line(nodes[i], nodes[i + 1]))
    lines.append(Line(nodes[-1], nodes[0]))  # close the loop
    geo.lines = lines

    problem.create_geometry(geo)

    # --- Material: Aluminum ---
    aluminum = HeatFlowMaterial(
        material_name="Aluminum", kx=200.0, ky=200.0, qv=0.0, kt=0.0
    )
    problem.add_material(aluminum)

    # ONE block label inside the base (entire heat sink is one region)
    label = Node(base_w / 2, base_h / 2)
    problem.define_block_label(label, aluminum)

    # --- Boundary Conditions ---
    # Heat flux at contact: P=10W, A=4mm*100mm=400mm^2=4e-4m^2, qs=25000 W/m^2
    heat_source = HeatFlowHeatFlux(name="HeatSource", qs=-25000.0)
    heat_source.Tset = 0
    heat_source.Tinf = 0
    heat_source.h = 0
    heat_source.beta = 0
    problem.add_boundary(heat_source)

    # Convection: h=10 W/(m^2*K), T_ambient=298K
    convection = HeatFlowConvection(name="AirConvection", Tinf=298.0, h=10.0)
    convection.Tset = 0
    convection.qs = 0
    convection.beta = 0
    problem.add_boundary(convection)

    # Assign BCs to segments
    # Contact segment: nodes[1] -> nodes[2]
    contact_seg = Line(nodes[1], nodes[2])
    problem.set_boundary_definition_segment(contact_seg.selection_point(), heat_source, elementsize=1)

    # All OTHER outline segments get convection
    for i in range(len(nodes)):
        j = (i + 1) % len(nodes)
        seg = Line(nodes[i], nodes[j])
        # Skip the contact segment (nodes[1]->nodes[2])
        if i == 1:
            continue
        problem.set_boundary_definition_segment(seg.selection_point(), convection, elementsize=1)

    # --- Analysis ---
    problem.make_analysis("planar")

    # Point values at key locations
    problem.get_point_values(Node(base_w / 2, 0))              # contact center
    problem.get_point_values(Node(base_w / 2, base_h / 2))    # base center
    problem.get_point_values(Node(fin_w / 2, base_h + fin_h)) # fin tip

    # Average temperature (raw Lua — no HeatFlowVolumeIntegral enum yet)
    problem.lua_script.append(f"ho_selectblock({base_w / 2}, {base_h / 2})")
    problem.lua_script.append("avg_T = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")
    problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')

    return problem


def main():
    parser = argparse.ArgumentParser(description="Heat sink thermal analysis")
    parser.add_argument("--run", action="store_true", help="Execute in FEMM")
    parser.add_argument("--output", default="heatsink.lua", help="Output Lua file")
    args = parser.parse_args()

    print("Building heat sink model...")
    print("  10W on 4mm contact, h=10 W/(m^2*K), T_amb=298K")
    print("  Expected: T ~ 356K, R_th ~ 5.8 K/W")

    problem = build_heatsink_problem()

    output_dir = Path(__file__).parent
    lua_file = output_dir / args.output
    problem.write(str(lua_file))
    print(f"Lua script: {lua_file} ({len(problem.lua_script)} lines)")

    if args.run:
        from py2femm_server.executor import FemmExecutor

        femm_path = Path("C:/femm42/bin/femm.exe")
        if not femm_path.exists():
            print("FEMM not found at C:/femm42/bin/femm.exe")
            return

        lua_script = "\n".join(problem.lua_script)
        executor = FemmExecutor(femm_path=femm_path, workspace=output_dir / "workspace")

        print("\nRunning FEMM...")
        csv_data, returncode = executor.run(lua_script, timeout=120)
        print(f"Return code: {returncode}")

        # Check for error logs
        import glob
        for job_dir in sorted((output_dir / "workspace").glob("job_*")):
            err = executor.read_error_log(job_dir)
            if err:
                print(f"\n{err}")

        if returncode == 0:
            for csv_file in output_dir.glob("*.csv"):
                print(f"\n--- {csv_file.name} ---")
                content = csv_file.read_text(encoding="utf-8")
                print(content[:1000])
        else:
            print("FEMM failed. Check workspace/job_*/error.log")


if __name__ == "__main__":
    main()
