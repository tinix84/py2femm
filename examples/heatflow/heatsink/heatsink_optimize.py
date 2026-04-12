"""2-Chip Placement Optimization on a Rectangular Heat Sink.

Finds optimal (x, y) positions of two heat sources on a finned
rectangular heat sink to minimize a weighted sum of thermal resistances.

Objective:  minimize  w_A * R_th_A  +  w_B * R_th_B
Variables:  (x_A, y_A, x_B, y_B)
Constraints:
  - Each chip stays inside the base with margin >= min_border_gap
  - Chips don't overlap: center distance >= min_chip_gap + chip size

Methods:
  - Brute-force grid search  (visualize full design space)
  - scipy.optimize.minimize  (Nelder-Mead, refine from best grid point)

Usage:
    python examples/heatflow/heatsink/heatsink_optimize.py
    python examples/heatflow/heatsink/heatsink_optimize.py --start-server
    python examples/heatflow/heatsink/heatsink_optimize.py --grid-n 8 --max-iter 30
    python examples/heatflow/heatsink/heatsink_optimize.py --no-plot --no-scipy
"""

from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from py2femm.client import FemmClient
from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Node, Line
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial


# ═══════════════════════════════════════════════════════════════════
# Configuration dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ChipConfig:
    """Heat source (chip) parameters."""
    name: str = "ChipA"
    width: float = 10.0     # mm
    height: float = 10.0    # mm
    power: float = 5.0      # W


@dataclass
class HeatsinkConfig:
    """Heat sink geometry and thermal parameters.

    The FEMM model is 2D planar:
      - base_w  = cross-section width (x axis in FEMM)
      - base_t  = base plate thickness (y axis in FEMM)
      - depth   = extrusion into the page (set to base_h for a rectangular plate)
    """
    # Base plate (A4 default: 210 x 297 mm)
    base_w: float = 210.0   # mm  cross-section width (short edge)
    base_h: float = 297.0   # mm  plate length (long edge, = extrusion depth)
    base_t: float = 5.0     # mm  base thickness

    # Fins (uniform across top surface, scaled for base_w)
    fin_w: float = 3.0      # mm
    fin_h: float = 20.0     # mm
    n_fins: int = 20

    # Thermal
    k_alu: float = 200.0    # W/(m*K)
    h_conv: float = 10.0    # W/(m^2*K)
    T_amb: float = 298.0    # K

    @property
    def depth(self) -> float:
        """Extrusion depth = plate length (base_h)."""
        return self.base_h


@dataclass
class OptimConfig:
    """Optimization parameters."""
    chip_a: ChipConfig = field(default_factory=lambda: ChipConfig(name="ChipA", power=5.0))
    chip_b: ChipConfig = field(default_factory=lambda: ChipConfig(name="ChipB", power=15.0))
    heatsink: HeatsinkConfig = field(default_factory=HeatsinkConfig)

    # Constraints
    min_border_gap: float = 5.0   # mm  min distance chip edge to base edge
    min_chip_gap: float = 5.0     # mm  min distance between chip edges

    # Objective weights
    weight_a: float = 0.5
    weight_b: float = 0.5

    # Brute-force grid
    grid_n: int = 10              # points per axis

    # Scipy
    max_iter: int = 50

    # FEMM
    timeout: int = 300            # seconds per simulation


# ═══════════════════════════════════════════════════════════════════
# Server management
# ═══════════════════════════════════════════════════════════════════

HEALTH_URL = "http://localhost:8082/api/v1/health"


def server_is_healthy() -> bool:
    try:
        resp = urllib.request.urlopen(HEALTH_URL, timeout=2)
        return json.loads(resp.read()).get("status") == "ok"
    except Exception:
        return False


def start_server():
    if server_is_healthy():
        print("[server] Already running.")
        return
    repo = Path(__file__).resolve().parent
    while repo.name and not (repo / "start_femm_server.bat").exists():
        repo = repo.parent
    bat = repo / "start_femm_server.bat"
    assert bat.exists(), f"start_femm_server.bat not found"
    print(f"[server] Launching {bat}")
    subprocess.Popen(
        ["cmd", "/c", str(bat)], cwd=str(repo),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    for _ in range(30):
        time.sleep(1)
        if server_is_healthy():
            print("[server] Ready.")
            return
    raise RuntimeError("Server did not start within 30s")


# ═══════════════════════════════════════════════════════════════════
# FEMM model builder
# ═══════════════════════════════════════════════════════════════════

def build_model(cfg: OptimConfig, x_a: float, y_a: float,
                x_b: float, y_b: float) -> str:
    """Build FEMM heat flow problem with 2 chips at given positions.

    Returns the Lua script as a string.

    The geometry is a rectangular base plate (no explicit fins — the
    convection coefficient h_conv should represent the effective fin-enhanced
    value).  Two heat-flux patches (chips) sit on the bottom surface.
    All other surfaces get convection BCs.

    This keeps the mesh small (~seconds per solve) so the optimizer
    can run hundreds of evaluations.
    """
    hs = cfg.heatsink
    ca, cb = cfg.chip_a, cfg.chip_b

    problem = FemmProblem(out_file="opt_results.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS, type="planar",
        precision=1e-8, depth=hs.depth, minangle=30,
    )

    # --- Build outline ---
    # Sort chips left-to-right for consistent segment ordering.
    chips = [
        ("A", ca, x_a - ca.width / 2, x_a + ca.width / 2),
        ("B", cb, x_b - cb.width / 2, x_b + cb.width / 2),
    ]
    chips.sort(key=lambda c: c[2])

    # Bottom edge nodes (y=0), split at each chip contact
    bottom_nodes = [Node(0, 0)]
    for label, chip, x_left, x_right in chips:
        if x_left > bottom_nodes[-1].x + 1e-6:
            bottom_nodes.append(Node(x_left, 0))
        bottom_nodes.append(Node(x_right, 0))
    if hs.base_w > bottom_nodes[-1].x + 1e-6:
        bottom_nodes.append(Node(hs.base_w, 0))

    # Simple rectangle: bottom -> right -> top -> left
    nodes = list(bottom_nodes)
    nodes.append(Node(hs.base_w, hs.base_t))
    nodes.append(Node(0, hs.base_t))

    # Deduplicate
    deduped = [nodes[0]]
    for n in nodes[1:]:
        if abs(n.x - deduped[-1].x) > 1e-6 or abs(n.y - deduped[-1].y) > 1e-6:
            deduped.append(n)
    if abs(deduped[-1].x - deduped[0].x) < 1e-6 and abs(deduped[-1].y - deduped[0].y) < 1e-6:
        deduped.pop()
    nodes = deduped

    geo = Geometry()
    geo.nodes = list(nodes)
    geo.lines = [Line(nodes[i], nodes[(i + 1) % len(nodes)]) for i in range(len(nodes))]
    problem.create_geometry(geo)

    # --- Material ---
    aluminum = HeatFlowMaterial(
        material_name="Aluminum", kx=hs.k_alu, ky=hs.k_alu, qv=0.0, kt=0.0
    )
    problem.add_material(aluminum)
    problem.define_block_label(Node(hs.base_w / 2, hs.base_t / 2), aluminum)

    # --- Boundary conditions ---
    # Heat flux for each chip
    chip_midpoints = set()
    for label, chip, x_left, x_right in chips:
        qs_chip = chip.power / (chip.width * hs.depth * 1e-6)  # W/m^2
        bc = HeatFlowHeatFlux(name=f"Heat_{label}", qs=-qs_chip)
        bc.Tset = 0; bc.Tinf = 0; bc.h = 0; bc.beta = 0
        problem.add_boundary(bc)
        seg_mid_x = (x_left + x_right) / 2
        problem.set_boundary_definition_segment(
            Node(seg_mid_x, 0), bc, elementsize=1
        )
        chip_midpoints.add(round(seg_mid_x, 6))

    # Convection on all other segments
    convection = HeatFlowConvection(name="AirConvection", Tinf=hs.T_amb, h=hs.h_conv)
    convection.Tset = 0; convection.qs = 0; convection.beta = 0
    problem.add_boundary(convection)

    for i in range(len(nodes)):
        j = (i + 1) % len(nodes)
        seg = Line(nodes[i], nodes[j])
        mid = seg.selection_point()
        if abs(mid.y) < 1e-6 and round(mid.x, 6) in chip_midpoints:
            continue
        problem.set_boundary_definition_segment(mid, convection, elementsize=1)

    # --- Analysis ---
    problem.make_analysis("planar")

    # Temperature at each chip center
    for label, chip, x_left, x_right in chips:
        cx = (x_left + x_right) / 2
        problem.get_point_values(Node(cx, 0))

    # Average temperature via block integral
    problem.lua_script.append(f"ho_selectblock({hs.base_w / 2}, {hs.base_t / 2})")
    problem.lua_script.append("avg_T = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")
    problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')

    # Chip temperatures
    for label, chip, x_left, x_right in chips:
        cx = (x_left + x_right) / 2
        problem.lua_script.append(f"T_{label} = ho_getpointvalues({cx}, 0)")
        problem.lua_script.append(
            f'write(file_out, "T_{label}_K = ", T_{label}, "\\n")'
        )

    problem.close()
    return "\n".join(problem.lua_script)


# ═══════════════════════════════════════════════════════════════════
# Constraint checking
# ═══════════════════════════════════════════════════════════════════

def is_feasible(cfg: OptimConfig, x_a: float, y_a: float,
                x_b: float, y_b: float) -> bool:
    """Check placement constraints."""
    hs = cfg.heatsink
    ca, cb = cfg.chip_a, cfg.chip_b
    mg = cfg.min_border_gap

    # Chip A within base
    if (x_a - ca.width / 2 < mg or x_a + ca.width / 2 > hs.base_w - mg):
        return False
    # Chip B within base
    if (x_b - cb.width / 2 < mg or x_b + cb.width / 2 > hs.base_w - mg):
        return False

    # Non-overlap: min edge-to-edge distance
    dx = abs(x_a - x_b) - (ca.width + cb.width) / 2
    if dx < cfg.min_chip_gap:
        return False

    return True


# ═══════════════════════════════════════════════════════════════════
# Single evaluation
# ═══════════════════════════════════════════════════════════════════

def parse_results(raw_csv: str) -> dict:
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


def evaluate(cfg: OptimConfig, client: FemmClient,
             x_a: float, y_a: float, x_b: float, y_b: float) -> dict | None:
    """Run one FEMM simulation, return results dict or None on failure."""
    if not is_feasible(cfg, x_a, y_a, x_b, y_b):
        return None

    lua = build_model(cfg, x_a, y_a, x_b, y_b)
    result = client.run(lua, timeout=cfg.timeout)
    if result.error or not result.csv_data:
        return None

    parsed = parse_results(result.csv_data)
    # Compute R_th for each chip
    hs = cfg.heatsink
    T_A = parsed.get("T_A_K")
    T_B = parsed.get("T_B_K")
    if T_A is None or T_B is None:
        return None

    parsed["R_th_A"] = (T_A - hs.T_amb) / cfg.chip_a.power
    parsed["R_th_B"] = (T_B - hs.T_amb) / cfg.chip_b.power
    parsed["objective"] = cfg.weight_a * parsed["R_th_A"] + cfg.weight_b * parsed["R_th_B"]
    return parsed


# ═══════════════════════════════════════════════════════════════════
# Brute-force grid search
# ═══════════════════════════════════════════════════════════════════

def brute_force(cfg: OptimConfig, client: FemmClient) -> list[dict]:
    """Grid search over chip placements. Returns list of evaluated points."""
    hs = cfg.heatsink
    ca, cb = cfg.chip_a, cfg.chip_b
    mg = cfg.min_border_gap

    # Valid x ranges for each chip
    x_min_a = mg + ca.width / 2
    x_max_a = hs.base_w - mg - ca.width / 2
    x_min_b = mg + cb.width / 2
    x_max_b = hs.base_w - mg - cb.width / 2

    xs_a = np.linspace(x_min_a, x_max_a, cfg.grid_n)
    xs_b = np.linspace(x_min_b, x_max_b, cfg.grid_n)

    # y is fixed at 0 (bottom surface) for 2D planar — chips sit on bottom edge
    y_a, y_b = 0.0, 0.0

    results = []
    total = len(xs_a) * len(xs_b)
    evaluated = 0
    skipped = 0

    print(f"\n=== Brute-Force Grid ({cfg.grid_n}x{cfg.grid_n} = {total} combinations) ===")

    for i, xa in enumerate(xs_a):
        for j, xb in enumerate(xs_b):
            if not is_feasible(cfg, xa, y_a, xb, y_b):
                skipped += 1
                continue

            evaluated += 1
            print(f"  [{evaluated}/{total - skipped}] xA={xa:.1f}, xB={xb:.1f}...", end=" ")

            res = evaluate(cfg, client, xa, y_a, xb, y_b)
            if res:
                res["x_a"] = xa
                res["x_b"] = xb
                results.append(res)
                print(f"R_thA={res['R_th_A']:.3f}, R_thB={res['R_th_B']:.3f}, obj={res['objective']:.3f}")
            else:
                print("FAILED")

    print(f"\n  Evaluated: {evaluated}, Skipped (infeasible): {skipped}")
    if results:
        best = min(results, key=lambda r: r["objective"])
        print(f"  Best: xA={best['x_a']:.1f}, xB={best['x_b']:.1f}, "
              f"obj={best['objective']:.3f}")

    return results


# ═══════════════════════════════════════════════════════════════════
# Scipy optimization
# ═══════════════════════════════════════════════════════════════════

def scipy_optimize(cfg: OptimConfig, client: FemmClient,
                   x0: tuple[float, float] | None = None) -> dict | None:
    """Nelder-Mead optimization of chip placement."""
    from scipy.optimize import minimize

    hs = cfg.heatsink
    ca, cb = cfg.chip_a, cfg.chip_b
    mg = cfg.min_border_gap

    if x0 is None:
        # Default: chips at 1/3 and 2/3 along the base
        x0 = (hs.base_w / 3, 2 * hs.base_w / 3)

    eval_count = [0]
    best_result = [None]

    def objective(x):
        xa, xb = x
        eval_count[0] += 1
        print(f"  [scipy #{eval_count[0]}] xA={xa:.1f}, xB={xb:.1f}...", end=" ")

        res = evaluate(cfg, client, xa, 0.0, xb, 0.0)
        if res is None:
            print("INFEASIBLE")
            return 1e6  # penalty
        print(f"obj={res['objective']:.3f}")

        if best_result[0] is None or res["objective"] < best_result[0]["objective"]:
            best_result[0] = {**res, "x_a": xa, "x_b": xb}
        return res["objective"]

    bounds_a = (mg + ca.width / 2, hs.base_w - mg - ca.width / 2)
    bounds_b = (mg + cb.width / 2, hs.base_w - mg - cb.width / 2)

    print(f"\n=== Scipy Nelder-Mead (max {cfg.max_iter} iter) ===")
    print(f"  x0 = ({x0[0]:.1f}, {x0[1]:.1f})")

    result = minimize(
        objective, x0, method="Nelder-Mead",
        options={"maxiter": cfg.max_iter, "xatol": 1.0, "fatol": 0.01},
    )

    print(f"\n  Converged: {result.success}, evaluations: {eval_count[0]}")
    if best_result[0]:
        b = best_result[0]
        print(f"  Best: xA={b['x_a']:.1f}, xB={b['x_b']:.1f}, obj={b['objective']:.3f}")
        print(f"         R_thA={b['R_th_A']:.3f} K/W, R_thB={b['R_th_B']:.3f} K/W")

    return best_result[0]


# ═══════════════════════════════════════════════════════════════════
# Plotting
# ═══════════════════════════════════════════════════════════════════

def plot_grid_results(cfg: OptimConfig, grid_results: list[dict],
                      scipy_result: dict | None = None):
    """Plot brute-force results: objective heatmap + Pareto front."""
    import matplotlib.pyplot as plt

    if not grid_results:
        print("No grid results to plot.")
        return

    xa = np.array([r["x_a"] for r in grid_results])
    xb = np.array([r["x_b"] for r in grid_results])
    obj = np.array([r["objective"] for r in grid_results])
    rth_a = np.array([r["R_th_A"] for r in grid_results])
    rth_b = np.array([r["R_th_B"] for r in grid_results])

    best_idx = np.argmin(obj)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. Objective scatter (xA vs xB colored by objective)
    ax1 = axes[0]
    sc = ax1.scatter(xa, xb, c=obj, cmap="viridis_r", s=60, edgecolors="black", linewidths=0.5)
    ax1.scatter(xa[best_idx], xb[best_idx], c="red", s=200, marker="*",
                zorder=5, label=f"Best (obj={obj[best_idx]:.3f})")
    if scipy_result:
        ax1.scatter(scipy_result["x_a"], scipy_result["x_b"], c="magenta", s=200,
                    marker="D", zorder=5, label=f"Scipy (obj={scipy_result['objective']:.3f})")
    plt.colorbar(sc, ax=ax1, label=f"{cfg.weight_a}*R_thA + {cfg.weight_b}*R_thB [K/W]")
    ax1.set_xlabel("Chip A position x [mm]")
    ax1.set_ylabel("Chip B position x [mm]")
    ax1.set_title("Objective Function")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # 2. Pareto front (R_th_A vs R_th_B)
    ax2 = axes[1]
    ax2.scatter(rth_a, rth_b, c=obj, cmap="viridis_r", s=60, edgecolors="black", linewidths=0.5)
    ax2.scatter(rth_a[best_idx], rth_b[best_idx], c="red", s=200, marker="*",
                zorder=5, label="Best (grid)")
    if scipy_result:
        ax2.scatter(scipy_result["R_th_A"], scipy_result["R_th_B"], c="magenta", s=200,
                    marker="D", zorder=5, label="Best (scipy)")

    # Pareto front extraction
    pareto_mask = np.ones(len(rth_a), dtype=bool)
    for i in range(len(rth_a)):
        for j in range(len(rth_a)):
            if i != j and rth_a[j] <= rth_a[i] and rth_b[j] <= rth_b[i] and (
                    rth_a[j] < rth_a[i] or rth_b[j] < rth_b[i]):
                pareto_mask[i] = False
                break
    if pareto_mask.any():
        pareto_idx = np.where(pareto_mask)[0]
        order = np.argsort(rth_a[pareto_idx])
        ax2.plot(rth_a[pareto_idx][order], rth_b[pareto_idx][order],
                 "r--", linewidth=1.5, label="Pareto front")

    ax2.set_xlabel("R_th_A [K/W]")
    ax2.set_ylabel("R_th_B [K/W]")
    ax2.set_title("Pareto Front")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # 3. Heat sink schematic with best placement
    ax3 = axes[2]
    hs = cfg.heatsink
    base = plt.Rectangle((0, 0), hs.base_w, hs.base_t, fill=True,
                          facecolor="silver", edgecolor="black", alpha=0.3)
    ax3.add_patch(base)

    # Draw fins
    gap = (hs.base_w - hs.n_fins * hs.fin_w) / max(hs.n_fins - 1, 1)
    for i in range(hs.n_fins):
        xl = i * (hs.fin_w + gap)
        fin = plt.Rectangle((xl, hs.base_t), hs.fin_w, hs.fin_h,
                             facecolor="silver", edgecolor="black", alpha=0.3)
        ax3.add_patch(fin)

    # Best chips (grid)
    ca, cb = cfg.chip_a, cfg.chip_b
    bx_a, bx_b = xa[best_idx], xb[best_idx]
    chip_a_rect = plt.Rectangle((bx_a - ca.width / 2, -ca.height / 2),
                                 ca.width, ca.height / 2,
                                 facecolor="red", edgecolor="black", alpha=0.7)
    chip_b_rect = plt.Rectangle((bx_b - cb.width / 2, -cb.height / 2),
                                 cb.width, cb.height / 2,
                                 facecolor="orange", edgecolor="black", alpha=0.7)
    ax3.add_patch(chip_a_rect)
    ax3.add_patch(chip_b_rect)
    ax3.text(bx_a, -ca.height / 2 - 2, f"A ({ca.power}W)", ha="center", fontsize=8, color="red")
    ax3.text(bx_b, -cb.height / 2 - 2, f"B ({cb.power}W)", ha="center", fontsize=8, color="orange")

    ax3.set_xlim(-10, hs.base_w + 10)
    ax3.set_ylim(-15, hs.base_t + hs.fin_h + 5)
    ax3.set_aspect("equal")
    ax3.set_xlabel("x [mm]")
    ax3.set_title("Best Placement (grid)")
    ax3.grid(True, alpha=0.3)

    plt.suptitle("2-Chip Placement Optimization", fontsize=14)
    plt.tight_layout()
    plt.show()


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="2-chip heat sink placement optimization")
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--no-scipy", action="store_true")
    parser.add_argument("--grid-n", type=int, default=10)
    parser.add_argument("--max-iter", type=int, default=50)
    parser.add_argument("--base-w", type=float, default=210.0)
    parser.add_argument("--base-h", type=float, default=297.0)
    parser.add_argument("--power-a", type=float, default=5.0)
    parser.add_argument("--power-b", type=float, default=15.0)
    parser.add_argument("--weight-a", type=float, default=0.5)
    parser.add_argument("--weight-b", type=float, default=0.5)
    parser.add_argument("--timeout", type=int, default=300, help="Seconds per FEMM run")
    args = parser.parse_args()

    # Build config
    cfg = OptimConfig(
        chip_a=ChipConfig(name="ChipA", power=args.power_a),
        chip_b=ChipConfig(name="ChipB", power=args.power_b),
        heatsink=HeatsinkConfig(base_w=args.base_w, base_h=args.base_h),
        weight_a=args.weight_a,
        weight_b=args.weight_b,
        grid_n=args.grid_n,
        max_iter=args.max_iter,
        timeout=args.timeout,
    )

    # Server
    if args.start_server:
        start_server()
    else:
        assert server_is_healthy(), (
            "py2femm server not running. Use --start-server or run start_femm_server.bat"
        )
        print("[server] OK")

    print(f"\nConfig:")
    print(f"  Base: {cfg.heatsink.base_w} x {cfg.heatsink.base_h} mm")
    print(f"  ChipA: {cfg.chip_a.width}x{cfg.chip_a.height} mm, {cfg.chip_a.power} W")
    print(f"  ChipB: {cfg.chip_b.width}x{cfg.chip_b.height} mm, {cfg.chip_b.power} W")
    print(f"  Weights: ({cfg.weight_a}, {cfg.weight_b})")
    print(f"  Grid: {cfg.grid_n}x{cfg.grid_n}, Scipy max_iter: {cfg.max_iter}")

    client = FemmClient(mode="remote", url="http://localhost:8082")

    # Brute-force
    grid_results = brute_force(cfg, client)

    # Scipy (start from best grid point)
    scipy_result = None
    if not args.no_scipy and grid_results:
        best_grid = min(grid_results, key=lambda r: r["objective"])
        scipy_result = scipy_optimize(cfg, client,
                                       x0=(best_grid["x_a"], best_grid["x_b"]))

    # Plot
    if not args.no_plot:
        plot_grid_results(cfg, grid_results, scipy_result)

    # Summary
    print("\n=== Summary ===")
    if grid_results:
        best = min(grid_results, key=lambda r: r["objective"])
        print(f"  Grid best:  xA={best['x_a']:.1f} mm, xB={best['x_b']:.1f} mm, "
              f"R_thA={best['R_th_A']:.3f}, R_thB={best['R_th_B']:.3f}, "
              f"obj={best['objective']:.3f}")
    if scipy_result:
        s = scipy_result
        print(f"  Scipy best: xA={s['x_a']:.1f} mm, xB={s['x_b']:.1f} mm, "
              f"R_thA={s['R_th_A']:.3f}, R_thB={s['R_th_B']:.3f}, "
              f"obj={s['objective']:.3f}")


if __name__ == "__main__":
    main()
