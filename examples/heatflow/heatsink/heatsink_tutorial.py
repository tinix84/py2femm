"""Heat Sink Thermal Analysis — Interactive Tutorial.

Complete py2femm workflow:
  0. Start the py2femm REST server (via start_femm_server.bat)
  1. Define dimensions and compute heat flux
  2. Build the heat sink geometry (5-fin closed polygon)
  3. Plot the geometry with boundary condition annotations
  4. Set up FEMM problem: material, BCs, analysis
  5. Generate the Lua script
  6. Submit to FEMM via py2femm server
  7. Parse and validate results
  8. Plot temperature summary
  9. Parametric study: sweep fin count (3, 5, 7, 9)

Usage:
    # With server already running:
    python examples/heatflow/heatsink/heatsink_tutorial.py

    # Auto-start the server:
    python examples/heatflow/heatsink/heatsink_tutorial.py --start-server

    # Keep FEMM visible for debugging:
    python examples/heatflow/heatsink/heatsink_tutorial.py --start-server --show-femm

    # Skip plots (CI / headless):
    python examples/heatflow/heatsink/heatsink_tutorial.py --no-plot

Translated from the FEMM heat flow tutorial video:
https://www.youtube.com/watch?v=1I1mQAT1Kts
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Server management
# ---------------------------------------------------------------------------

AGENT_URL = "http://localhost:8082/api/v1/health"


def server_is_healthy() -> bool:
    try:
        resp = urllib.request.urlopen(AGENT_URL, timeout=2)
        data = json.loads(resp.read())
        return data.get("status") == "ok"
    except Exception:
        return False


def start_server(show_femm: bool = False) -> subprocess.Popen | None:
    """Launch start_femm_server.bat and wait for the REST API."""
    if server_is_healthy():
        print("[server] Already running.")
        return None

    repo_root = Path(__file__).resolve().parent
    while repo_root.name and not (repo_root / "start_femm_server.bat").exists():
        repo_root = repo_root.parent
    bat = repo_root / "start_femm_server.bat"
    assert bat.exists(), f"start_femm_server.bat not found (searched up from {Path(__file__).parent})"

    print(f"[server] Launching: {bat}")
    proc = subprocess.Popen(
        ["cmd", "/c", str(bat)],
        cwd=str(repo_root),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for _ in range(30):
        time.sleep(1)
        if server_is_healthy():
            print("[server] Ready.")
            return proc
    raise RuntimeError("py2femm server did not start within 30s")


# ---------------------------------------------------------------------------
# 1. Dimensions
# ---------------------------------------------------------------------------

# Geometry [mm]
BASE_W = 35.0
BASE_H = 5.0
FIN_W = 1.5
FIN_H = 20.0
N_FINS = 5
DEPTH = 100.0  # extrusion depth

GAP = (BASE_W - N_FINS * FIN_W) / (N_FINS - 1)

CONTACT_W = 4.0
CX0 = (BASE_W - CONTACT_W) / 2.0
CX1 = CX0 + CONTACT_W

# Thermal
P = 10.0                              # total power [W]
A_CONTACT = CONTACT_W * DEPTH * 1e-6  # contact area [m^2]
QS = P / A_CONTACT                    # heat flux [W/m^2]
H_CONV = 10.0                         # convection coeff [W/(m^2*K)]
T_AMB = 298.0                         # ambient temperature [K]


def print_dimensions():
    print("\n=== 1. Dimensions ===")
    print(f"  Base:     {BASE_W} x {BASE_H} mm")
    print(f"  Fins:     {N_FINS} x {FIN_W} mm wide, {FIN_H} mm tall, gap = {GAP:.3f} mm")
    print(f"  Contact:  {CONTACT_W} mm centered ({CX0} - {CX1} mm)")
    print(f"  Depth:    {DEPTH} mm")
    print(f"  Power:    {P} W  ->  qs = {QS:.0f} W/m^2")
    print(f"  Convection: h = {H_CONV} W/(m^2*K), T_amb = {T_AMB} K")


# ---------------------------------------------------------------------------
# 2. Geometry
# ---------------------------------------------------------------------------

from py2femm.geometry import Geometry, Node, Line  # noqa: E402


def build_outline_nodes() -> list[Node]:
    """Build closed polygon nodes for the heat sink cross-section."""
    nodes = [
        Node(0, 0),
        Node(CX0, 0),
        Node(CX1, 0),
        Node(BASE_W, 0),
        Node(BASE_W, BASE_H),
    ]
    for i in range(N_FINS - 1, -1, -1):
        x_left = i * (FIN_W + GAP)
        x_right = x_left + FIN_W
        nodes.extend([
            Node(x_right, BASE_H),
            Node(x_right, BASE_H + FIN_H),
            Node(x_left, BASE_H + FIN_H),
            Node(x_left, BASE_H),
        ])
    # Deduplicate consecutive nodes
    deduped = [nodes[0]]
    for n in nodes[1:]:
        if abs(n.x - deduped[-1].x) > 1e-6 or abs(n.y - deduped[-1].y) > 1e-6:
            deduped.append(n)
    if abs(deduped[-1].x - deduped[0].x) < 1e-6 and abs(deduped[-1].y - deduped[0].y) < 1e-6:
        deduped.pop()
    return deduped


def build_geometry(nodes: list[Node]) -> tuple[Geometry, list[Line]]:
    """Create Geometry with closed polygon from nodes."""
    geo = Geometry()
    geo.nodes = list(nodes)
    lines = [Line(nodes[i], nodes[(i + 1) % len(nodes)]) for i in range(len(nodes))]
    geo.lines = lines
    return geo, lines


# ---------------------------------------------------------------------------
# 3. Plot geometry
# ---------------------------------------------------------------------------

def plot_geometry(nodes: list[Node], lines: list[Line]):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 7))

    # All segments (convection = blue)
    for seg in lines:
        ax.plot([seg.start_pt.x, seg.end_pt.x],
                [seg.start_pt.y, seg.end_pt.y],
                color="steelblue", linewidth=1.5)

    # Heat source segment (red)
    ax.plot([nodes[1].x, nodes[2].x], [nodes[1].y, nodes[2].y],
            color="red", linewidth=3.5, label=f"Heat source ({QS:.0f} W/m\u00b2)")

    # Nodes
    ax.scatter([n.x for n in nodes], [n.y for n in nodes],
               color="black", s=15, zorder=5)

    # Fill
    xs = [n.x for n in nodes] + [nodes[0].x]
    ys = [n.y for n in nodes] + [nodes[0].y]
    ax.fill(xs, ys, alpha=0.15, color="silver", label="Aluminum (k=200 W/m\u00b7K)")

    # Block label
    ax.plot(BASE_W / 2, BASE_H / 2, "x", color="darkgreen", markersize=10, markeredgewidth=2)

    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title("Heat Sink Cross-Section")
    ax.set_aspect("equal")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# 4-5. Build FEMM problem and generate Lua
# ---------------------------------------------------------------------------

from py2femm.femm_problem import FemmProblem  # noqa: E402
from py2femm.general import LengthUnit  # noqa: E402
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial  # noqa: E402


def build_femm_problem(nodes: list[Node], geo: Geometry) -> FemmProblem:
    """Build the complete FEMM heat flow problem."""
    problem = FemmProblem(out_file="heatsink_data.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS, type="planar",
        precision=1e-8, depth=DEPTH, minangle=30,
    )
    problem.create_geometry(geo)

    # Material
    aluminum = HeatFlowMaterial(material_name="Aluminum", kx=200.0, ky=200.0, qv=0.0, kt=0.0)
    problem.add_material(aluminum)
    problem.define_block_label(Node(BASE_W / 2, BASE_H / 2), aluminum)

    # Boundary conditions
    heat_source = HeatFlowHeatFlux(name="HeatSource", qs=-QS)
    heat_source.Tset = 0; heat_source.Tinf = 0; heat_source.h = 0; heat_source.beta = 0
    problem.add_boundary(heat_source)

    convection = HeatFlowConvection(name="AirConvection", Tinf=T_AMB, h=H_CONV)
    convection.Tset = 0; convection.qs = 0; convection.beta = 0
    problem.add_boundary(convection)

    # Assign BCs
    contact_seg = Line(nodes[1], nodes[2])
    problem.set_boundary_definition_segment(contact_seg.selection_point(), heat_source, elementsize=1)
    for i in range(len(nodes)):
        if i == 1:
            continue  # contact patch already assigned
        seg = Line(nodes[i], nodes[(i + 1) % len(nodes)])
        if abs(seg.start_pt.y) < 1e-6 and abs(seg.end_pt.y) < 1e-6:
            continue  # bottom segment — insulated
        problem.set_boundary_definition_segment(seg.selection_point(), convection, elementsize=1)

    # Analysis + post-processing
    problem.make_analysis("planar")

    # Point values via raw Lua (get_point_values only supports magnetic field)
    contact_cx = (CX0 + CX1) / 2
    fin_tip_x = FIN_W / 2
    fin_tip_y = BASE_H + FIN_H

    problem.lua_script.append(f"T_contact = ho_getpointvalues({contact_cx}, 0)")
    problem.lua_script.append(f"T_base = ho_getpointvalues({BASE_W / 2}, {BASE_H / 2})")
    problem.lua_script.append(f"T_fintip = ho_getpointvalues({fin_tip_x}, {fin_tip_y})")

    # Block integral: average temperature
    problem.lua_script.append(f"ho_selectblock({BASE_W / 2}, {BASE_H / 2})")
    problem.lua_script.append("avg_T = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")

    # Bitmap capture: temperature contour plot
    # ho_showdensityplot(legend, gscale, type, upper, lower) — type 0 = temperature
    problem.lua_script.append("ho_showdensityplot(1, 0, 0, T_contact, T_fintip)")
    problem.lua_script.append('ho_savebitmap("heatsink_temperature.bmp")')

    # Write results to CSV
    problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')
    problem.lua_script.append('write(file_out, "T_contact_K = ", T_contact, "\\n")')
    problem.lua_script.append('write(file_out, "T_base_K = ", T_base, "\\n")')
    problem.lua_script.append('write(file_out, "T_fintip_K = ", T_fintip, "\\n")')

    return problem


def get_lua_script(problem: FemmProblem) -> str:
    problem.close()
    return "\n".join(problem.lua_script)


# ---------------------------------------------------------------------------
# 6. Execute in FEMM
# ---------------------------------------------------------------------------

from py2femm.client import FemmClient  # noqa: E402


def run_femm(lua_script: str) -> str:
    """Submit Lua to server, return raw CSV. Crashes on failure."""
    client = FemmClient(mode="remote", url="http://localhost:8082")
    print(f"  Connected (mode: {client._mode})")

    result = client.run(lua_script, timeout=120)
    assert result.error is None, f"FEMM execution failed: {result.error}"
    assert result.csv_data, "FEMM returned no CSV data"

    print(f"  Completed in {result.elapsed_s:.1f}s")
    return result.csv_data


# ---------------------------------------------------------------------------
# 7. Parse results
# ---------------------------------------------------------------------------

def parse_results(raw_csv: str) -> dict:
    """Parse key=value pairs from CSV output."""
    results = {}
    for line in raw_csv.strip().splitlines():
        line = line.strip()
        if not line or "=" not in line or line.startswith("x,"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().rstrip(",")
        try:
            results[key] = float(val)
        except ValueError:
            results[key] = val
    return results


def validate_results(results: dict) -> tuple[float, float]:
    """Extract avg_T and R_th, crash if missing."""
    assert "AverageTemperature_K" in results, (
        f"AverageTemperature_K not in results. Got: {list(results.keys())}"
    )
    avg_T = results["AverageTemperature_K"]
    R_th = (avg_T - T_AMB) / P
    return avg_T, R_th


# ---------------------------------------------------------------------------
# 8. Plot results
# ---------------------------------------------------------------------------

def plot_results(nodes: list[Node], avg_T: float, R_th: float):
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    # Left: geometry with temperature color
    ax1 = axes[0]
    norm = Normalize(vmin=T_AMB, vmax=avg_T + 10)
    cmap = plt.cm.hot_r

    base_rect = plt.Rectangle((0, 0), BASE_W, BASE_H, linewidth=0)
    base_rect.set_facecolor(cmap(norm(avg_T)))
    ax1.add_patch(base_rect)

    for i in range(N_FINS):
        x_left = i * (FIN_W + GAP)
        fin_rect = plt.Rectangle((x_left, BASE_H), FIN_W, FIN_H, linewidth=0)
        fin_T = avg_T - (avg_T - T_AMB) * 0.3
        fin_rect.set_facecolor(cmap(norm(fin_T)))
        ax1.add_patch(fin_rect)

    xs = [n.x for n in nodes] + [nodes[0].x]
    ys = [n.y for n in nodes] + [nodes[0].y]
    ax1.plot(xs, ys, "k-", linewidth=1.5)

    ax1.annotate("", xy=(BASE_W / 2, 1.5), xytext=(BASE_W / 2, -4),
                 arrowprops=dict(arrowstyle="-|>", color="red", lw=2.5))
    ax1.text(BASE_W / 2, -5.5, f"P = {P:.0f} W", ha="center", fontsize=10,
             color="red", weight="bold")

    for i in range(N_FINS):
        x_mid = i * (FIN_W + GAP) + FIN_W / 2
        ax1.annotate("", xy=(x_mid, BASE_H + FIN_H + 3), xytext=(x_mid, BASE_H + FIN_H),
                     arrowprops=dict(arrowstyle="-|>", color="steelblue", lw=1.5))
    ax1.text(BASE_W / 2, BASE_H + FIN_H + 4.5,
             f"h = {H_CONV} W/(m\u00b2\u00b7K), T\u221e = {T_AMB} K",
             ha="center", fontsize=9, color="steelblue")

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax1, shrink=0.7, pad=0.02).set_label("Temperature [K]")

    ax1.set_xlim(-5, BASE_W + 5)
    ax1.set_ylim(-8, BASE_H + FIN_H + 8)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x [mm]")
    ax1.set_ylabel("y [mm]")
    ax1.set_title("Heat Sink \u2014 Temperature Field")

    # Right: summary bar chart
    ax2 = axes[1]
    labels = ["T_ambient", "T_avg", "\u0394T"]
    values = [T_AMB, avg_T, avg_T - T_AMB]
    colors = ["steelblue", "orangered", "goldenrod"]
    bars = ax2.bar(labels, values, color=colors, edgecolor="black", linewidth=0.8)
    for bar, val in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                 f"{val:.1f} K", ha="center", fontsize=10, weight="bold")
    ax2.set_ylabel("Temperature [K]")
    ax2.set_title(f"Thermal Summary \u2014 R_th = {R_th:.2f} K/W")
    ax2.set_ylim(0, max(values) * 1.15)
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.show()


def load_femm_bitmap(bmp_path: str):
    """Load a BMP file saved by FEMM's ho_savebitmap(), return as numpy array.

    Usage in notebooks:
        img = load_femm_bitmap("path/to/heatsink_temperature.bmp")
        plt.imshow(img)
        plt.axis("off")
        plt.show()
    """
    from PIL import Image
    import numpy as np
    img = Image.open(bmp_path)
    return np.array(img)


# ---------------------------------------------------------------------------
# 9. Parametric study
# ---------------------------------------------------------------------------

def build_parametric(n_fins_param: int) -> str:
    """Build a heat sink with n_fins_param fins, return Lua script."""
    prob = FemmProblem(out_file="heatsink_data.csv")
    prob.heat_problem(units=LengthUnit.MILLIMETERS, type="planar",
                      precision=1e-8, depth=DEPTH, minangle=30)

    gap_p = (BASE_W - n_fins_param * FIN_W) / max(n_fins_param - 1, 1)
    ns = [Node(0, 0), Node(CX0, 0), Node(CX1, 0), Node(BASE_W, 0), Node(BASE_W, BASE_H)]
    for i in range(n_fins_param - 1, -1, -1):
        xl = i * (FIN_W + gap_p)
        xr = xl + FIN_W
        ns.extend([Node(xr, BASE_H), Node(xr, BASE_H + FIN_H),
                    Node(xl, BASE_H + FIN_H), Node(xl, BASE_H)])

    dd = [ns[0]]
    for n in ns[1:]:
        if abs(n.x - dd[-1].x) > 1e-6 or abs(n.y - dd[-1].y) > 1e-6:
            dd.append(n)
    if abs(dd[-1].x - dd[0].x) < 1e-6 and abs(dd[-1].y - dd[0].y) < 1e-6:
        dd.pop()
    ns = dd

    g = Geometry()
    g.nodes = list(ns)
    g.lines = [Line(ns[i], ns[(i + 1) % len(ns)]) for i in range(len(ns))]
    prob.create_geometry(g)

    al = HeatFlowMaterial(material_name="Aluminum", kx=200.0, ky=200.0, qv=0.0, kt=0.0)
    prob.add_material(al)
    prob.define_block_label(Node(BASE_W / 2, BASE_H / 2), al)

    hs = HeatFlowHeatFlux(name="HeatSource", qs=-QS)
    hs.Tset = 0; hs.Tinf = 0; hs.h = 0; hs.beta = 0
    prob.add_boundary(hs)

    cv = HeatFlowConvection(name="AirConvection", Tinf=T_AMB, h=H_CONV)
    cv.Tset = 0; cv.qs = 0; cv.beta = 0
    prob.add_boundary(cv)

    prob.set_boundary_definition_segment(Line(ns[1], ns[2]).selection_point(), hs, elementsize=1)
    for i in range(len(ns)):
        if i == 1:
            continue  # contact patch already assigned
        seg = Line(ns[i], ns[(i + 1) % len(ns)])
        if abs(seg.start_pt.y) < 1e-6 and abs(seg.end_pt.y) < 1e-6:
            continue  # bottom segment — insulated
        prob.set_boundary_definition_segment(seg.selection_point(), cv, elementsize=1)

    prob.make_analysis("planar")
    prob.lua_script.append(f"ho_selectblock({BASE_W / 2}, {BASE_H / 2})")
    prob.lua_script.append("avg_T = ho_blockintegral(0)")
    prob.lua_script.append("ho_clearblock()")
    prob.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')
    prob.close()
    return "\n".join(prob.lua_script)


def run_parametric(do_plot: bool = True):
    """Sweep fin count and plot results."""
    print("\n=== 9. Parametric Study ===")
    client = FemmClient(mode="remote", url="http://localhost:8082")
    fin_counts = [3, 5, 7, 9]
    parametric = {}

    for nf in fin_counts:
        print(f"  {nf} fins...", end=" ")
        script = build_parametric(nf)
        res = client.run(script, timeout=120)
        assert res.error is None, f"{nf}-fin case failed: {res.error}"
        assert res.csv_data, f"{nf}-fin case returned no CSV data"
        parsed = parse_results(res.csv_data)
        assert "AverageTemperature_K" in parsed, (
            f"{nf}-fin: AverageTemperature_K not in output"
        )
        T = parsed["AverageTemperature_K"]
        parametric[nf] = T
        print(f"T_avg = {T:.1f} K  (R_th = {(T - T_AMB) / P:.2f} K/W)")

    if do_plot and parametric:
        plot_parametric(parametric)


def plot_parametric(parametric: dict[int, float]):
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fins = sorted(parametric.keys())
    temps = [parametric[nf] for nf in fins]
    r_ths = [(T - T_AMB) / P for T in temps]

    ax1.plot(fins, temps, "ro-", markersize=8, linewidth=2)
    ax1.axhline(T_AMB, color="steelblue", linestyle="--", alpha=0.7,
                label=f"T_ambient = {T_AMB} K")
    for nf, T in zip(fins, temps):
        ax1.annotate(f"{T:.1f} K", (nf, T), textcoords="offset points",
                     xytext=(0, 10), ha="center", fontsize=9)
    ax1.set_xlabel("Number of fins")
    ax1.set_ylabel("Average temperature [K]")
    ax1.set_title("Temperature vs. Fin Count")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.bar(fins, r_ths, color="goldenrod", edgecolor="black", width=0.8)
    for nf, r in zip(fins, r_ths):
        ax2.text(nf, r + 0.1, f"{r:.2f}", ha="center", fontsize=10, weight="bold")
    ax2.set_xlabel("Number of fins")
    ax2.set_ylabel("Thermal resistance [K/W]")
    ax2.set_title("R_th vs. Fin Count")
    ax2.grid(axis="y", alpha=0.3)

    plt.suptitle("Parametric Study \u2014 Heat Sink Fin Count", fontsize=13)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Heat sink thermal tutorial")
    parser.add_argument("--start-server", action="store_true",
                        help="Launch start_femm_server.bat before running")
    parser.add_argument("--show-femm", action="store_true",
                        help="Keep FEMM window visible (only with --start-server)")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip matplotlib plots")
    parser.add_argument("--no-parametric", action="store_true",
                        help="Skip parametric sweep")
    args = parser.parse_args()

    do_plot = not args.no_plot

    # 0. Server
    server_proc = None
    if args.start_server:
        server_proc = start_server(show_femm=args.show_femm)
    else:
        assert server_is_healthy(), (
            "py2femm server not running on localhost:8082.\n"
            "  Start it with: start_femm_server.bat\n"
            "  Or pass --start-server to this script."
        )
        print("[server] Already running.")

    # 1. Dimensions
    print_dimensions()

    # 2. Geometry
    print("\n=== 2. Build Geometry ===")
    nodes = build_outline_nodes()
    geo, lines = build_geometry(nodes)
    print(f"  {len(nodes)} nodes, {len(lines)} segments")

    # 3. Plot geometry
    if do_plot:
        print("\n=== 3. Plot Geometry ===")
        plot_geometry(nodes, lines)

    # 4-5. FEMM problem + Lua
    print("\n=== 4. Build FEMM Problem ===")
    problem = build_femm_problem(nodes, geo)
    lua_script = get_lua_script(problem)
    print(f"  Lua script: {len(lua_script)} chars, {lua_script.count(chr(10))} lines")

    # Save Lua for inspection
    output_dir = Path(__file__).parent
    lua_file = output_dir / "heatsink_tutorial.lua"
    lua_file.write_text(lua_script, encoding="utf-8")
    print(f"  Saved to: {lua_file}")

    # 6. Execute
    print("\n=== 5. Execute in FEMM ===")
    csv_data = run_femm(lua_script)
    print(f"\n  Raw output:\n  {csv_data.strip()}")

    # 7. Parse
    print("\n=== 6. Parse Results ===")
    results = parse_results(csv_data)
    assert results, f"No results parsed from:\n{csv_data[:500]}"
    for k, v in results.items():
        print(f"  {k} = {v:.4f}" if isinstance(v, float) else f"  {k} = {v}")

    avg_T, R_th = validate_results(results)
    print(f"\n  Average temperature:  {avg_T:.1f} K  ({avg_T - 273.15:.1f} \u00b0C)")
    print(f"  Thermal resistance:   {R_th:.2f} K/W")
    print(f"  Expected:             ~356 K,  R_th ~ 5.8 K/W")

    # 8. Plot results
    if do_plot:
        print("\n=== 7. Plot Results ===")
        plot_results(nodes, avg_T, R_th)

    # 9. Parametric
    if not args.no_parametric:
        run_parametric(do_plot=do_plot)

    print("\nDone.")


if __name__ == "__main__":
    main()
