"""End-to-end example: Define geometry -> Generate Lua -> Submit to agent -> Plot results.

Demonstrates the full py2femm workflow:
1. Build a planar capacitor geometry using py2femm Python API
2. Generate a FEMM Lua script (FemmProblem)
3. Submit the script to the py2femm agent via FemmClient
4. Parse the CSV results into a DataFrame
5. Plot the results with matplotlib

Usage:
    # With agent running on Windows:
    python examples/02_e2e_capacitor_with_plot.py

    # Without agent (just generate Lua + show what would be submitted):
    python examples/02_e2e_capacitor_with_plot.py --dry-run
"""

import argparse
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

from py2femm.electrostatics import (
    ElectrostaticFixedVoltage,
    ElectrostaticMaterial,
    ElectrostaticSurfaceCharge,
    ElectrostaticVolumeIntegral,
)
from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import CircleArc, Geometry, Line, Node


# ---------------------------------------------------------------------------
# Step 1: Define the geometry and build the FEMM problem
# ---------------------------------------------------------------------------

def build_capacitor_problem(width: float, thickness: float, gap: float) -> FemmProblem:
    """Build a planar capacitor FemmProblem and return it (Lua not yet written)."""

    problem = FemmProblem(out_file="capacitor_data.csv")
    problem.electrostatic_problem(LengthUnit.METERS, "planar")

    # --- Geometry ---
    geo = Geometry()

    # Top electrode
    n1 = Node(-width / 2, gap / 2)
    n2 = Node(-width / 2, gap / 2 + thickness)
    n3 = Node(width / 2, gap / 2 + thickness)
    n4 = Node(width / 2, gap / 2)

    # Bottom electrode
    n5 = Node(-width / 2, -gap / 2)
    n6 = Node(-width / 2, -gap / 2 - thickness)
    n7 = Node(width / 2, -gap / 2 - thickness)
    n8 = Node(width / 2, -gap / 2)

    # Electrode lines
    lines_top = [Line(n1, n2), Line(n2, n3), Line(n3, n4), Line(n4, n1)]
    lines_bot = [Line(n5, n6), Line(n6, n7), Line(n7, n8), Line(n8, n5)]
    lines_gap = [Line(n1, n5), Line(n8, n4)]

    # Outer boundary (circular)
    r = 0.3
    out_top = Node(0.0, r)
    out_left = Node(-r, 0.0)
    out_bot = Node(0.0, -r)
    out_right = Node(r, 0.0)
    center = Node(0, 0)

    arcs = [
        CircleArc(out_top, center, out_left),
        CircleArc(out_left, center, out_bot),
        CircleArc(out_bot, center, out_right),
        CircleArc(out_right, center, out_top),
    ]

    geo.nodes = [n1, n2, n3, n4, n5, n6, n7, n8, out_top, out_left, out_bot, out_right]
    geo.lines = lines_top + lines_bot + lines_gap
    geo.circle_arcs = arcs

    problem.create_geometry(geo)

    # --- Materials ---
    epoxy = ElectrostaticMaterial(material_name="epoxy", ex=3.7, ey=3.7, qv=0.0)
    air = ElectrostaticMaterial(material_name="air", ex=1.0, ey=1.0, qv=0.0)
    metal = ElectrostaticMaterial(material_name="metal", ex=1.0, ey=1.0, qv=0.0)

    for mat in [epoxy, air, metal]:
        problem.add_material(mat)

    insulation_block = Node(0.0, 0.0)
    problem.define_block_label(insulation_block, epoxy)
    problem.define_block_label(Node(0.0, 0.2), air)
    problem.define_block_label(Node(0.0, gap / 2 + thickness / 2), metal)
    problem.define_block_label(Node(0.0, -gap / 2 - thickness / 2), metal)

    # --- Boundary conditions ---
    v0 = ElectrostaticFixedVoltage("U0", 10.0)
    gnd = ElectrostaticFixedVoltage("GND", 0.0)
    neumann = ElectrostaticSurfaceCharge("outline", 0.0)

    for bc in [neumann, gnd, v0]:
        problem.add_boundary(bc)

    for line in lines_top:
        problem.set_boundary_definition_segment(line.selection_point(), v0)
    for line in lines_bot:
        problem.set_boundary_definition_segment(line.selection_point(), gnd)
    for arc in arcs:
        problem.set_boundary_definition_segment(arc.selection_point(), neumann)

    # --- Analysis ---
    problem.make_analysis("planar")

    # Post-processing: stored energy and field averages
    problem.get_integral_values(
        [insulation_block], save_image=False, variable_name=ElectrostaticVolumeIntegral.StoredEnergy
    )
    problem.get_integral_values(
        [insulation_block], save_image=False, variable_name=ElectrostaticVolumeIntegral.AvgE
    )

    # Sample field along the gap centerline
    n_points = 20
    for i in range(n_points):
        y = -gap / 2 + (i + 0.5) * gap / n_points
        problem.get_point_values(Node(0.0, y))

    return problem


# ---------------------------------------------------------------------------
# Step 2: Generate the Lua script as a string
# ---------------------------------------------------------------------------

def get_lua_script(problem: FemmProblem) -> str:
    """Extract the Lua script from a FemmProblem as a string."""
    problem.close()
    return "\n".join(problem.lua_script)


# ---------------------------------------------------------------------------
# Step 3 & 4: Submit to agent and parse results
# ---------------------------------------------------------------------------

def submit_and_collect(lua_script: str) -> pd.DataFrame:
    """Submit Lua script to py2femm agent, return results as DataFrame."""
    from py2femm.client import FemmClient
    from py2femm.client.models import JobResult

    print("Connecting to py2femm agent...")
    client = FemmClient()
    print(f"  Mode: {client._mode}")

    print("Submitting Lua script...")
    result = client.run(lua_script, timeout=120)

    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)

    print(f"  Completed in {result.elapsed_s:.1f}s")

    job_result = JobResult(csv_data=result.csv_data)
    return job_result.to_dataframe()


# ---------------------------------------------------------------------------
# Step 5: Plot
# ---------------------------------------------------------------------------

def plot_results(df: pd.DataFrame, output_path: str = "capacitor_results.png"):
    """Plot the simulation results."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping plot. Install with: pip install matplotlib")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # If we have point value data with x, y columns, plot the field profile
    if "y" in df.columns and len(df) > 2:
        ax1 = axes[0]
        ax1.plot(df["y"] * 1000, df.iloc[:, 3], "b-o", markersize=4)
        ax1.set_xlabel("y position [mm]")
        ax1.set_ylabel(df.columns[3])
        ax1.set_title("Field along gap centerline")
        ax1.grid(True, alpha=0.3)

    # Bar chart of integral values if available
    ax2 = axes[1]
    integral_cols = [c for c in df.columns if c not in ("x", "y", "point")]
    if integral_cols and len(df) <= 5:
        ax2.bar(range(len(df)), df[integral_cols[0]])
        ax2.set_ylabel(integral_cols[0])
        ax2.set_title("Integral values")
        ax2.grid(True, alpha=0.3)

    plt.suptitle("py2femm Planar Capacitor Results", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Plot saved to {output_path}")
    plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="py2femm end-to-end capacitor example")
    parser.add_argument("--dry-run", action="store_true", help="Generate Lua only, don't submit")
    parser.add_argument("--width", type=float, default=0.2, help="Electrode width [m]")
    parser.add_argument("--thickness", type=float, default=0.005, help="Electrode thickness [m]")
    parser.add_argument("--gap", type=float, default=0.01, help="Gap between electrodes [m]")
    parser.add_argument("--output", type=str, default="capacitor.lua", help="Lua output file")
    args = parser.parse_args()

    print(f"Building capacitor: width={args.width}m, thickness={args.thickness}m, gap={args.gap}m")
    problem = build_capacitor_problem(args.width, args.thickness, args.gap)

    lua_script = get_lua_script(problem)
    print(f"Generated Lua script: {len(lua_script)} characters, {lua_script.count(chr(10))} lines")

    # Save Lua to file for inspection
    Path(args.output).write_text(lua_script, encoding="utf-8")
    print(f"Lua script saved to {args.output}")

    if args.dry_run:
        print("\n--dry-run: skipping submission. Review the generated Lua file.")
        return

    # Submit to agent and get results
    df = submit_and_collect(lua_script)
    print(f"\nResults ({len(df)} rows):")
    print(df.to_string(index=False))

    # Plot
    plot_results(df)


if __name__ == "__main__":
    main()
