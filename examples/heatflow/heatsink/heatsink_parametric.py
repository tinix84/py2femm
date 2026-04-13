"""Heatsink Parametric Study — Square-Wave Fin Parametrization.

Provides HeatsinkConfig dataclass, sweep grid generation, FEMM problem
builder, sweep engine, and visualization for a full factorial study of
heatsink fin geometry.

Usage:
    python examples/heatflow/heatsink/heatsink_parametric.py
    python examples/heatflow/heatsink/heatsink_parametric.py --start-server
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Line, Node
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial


# ---------------------------------------------------------------------------
# Thermal constants (shared with heatsink_tutorial.py)
# ---------------------------------------------------------------------------
P = 10.0             # total power [W]
H_CONV = 10.0        # convection coefficient [W/(m^2*K)]
T_AMB = 298.0        # ambient temperature [K]
DEPTH = 100.0        # extrusion depth [mm]
HEIGHT_TOTAL = 25.0  # total height (base + fin) [mm]
CONTACT_WIDTH = 4.0  # heat source width [mm]
SOURCE_WIDTH = 4.0   # source width for L grid [mm]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class HeatsinkConfig:
    """Square-wave parametrization of a heatsink cross-section.

    Primary parameters:
        base_width:    L — total heatsink width [mm]
        pitch:         p — target fin repetition distance [mm]
        duty_cycle:    D — fraction of pitch occupied by fin [0–1]
        base_ratio:    r_b — base height as fraction of total height [0–1]
        height_total:  H_tot — total height = base + fin [mm]
        contact_width: width of heat source patch [mm]
        contact_mode:  "centered", "single_fin", or "between_fins"
    """
    base_width: float
    pitch: float
    duty_cycle: float
    base_ratio: float
    height_total: float = HEIGHT_TOTAL
    contact_width: float = CONTACT_WIDTH
    contact_mode: str = "centered"

    # Derived (computed in __post_init__)
    n_fins: int = field(init=False)
    pitch_actual: float = field(init=False)
    fin_width: float = field(init=False)
    gap: float = field(init=False)
    base_height: float = field(init=False)
    fin_height: float = field(init=False)

    def __post_init__(self):
        self.n_fins = max(2, round(self.base_width / self.pitch))
        self.pitch_actual = self.base_width / self.n_fins
        self.fin_width = self.duty_cycle * self.pitch_actual
        self.gap = (1 - self.duty_cycle) * self.pitch_actual
        self.base_height = self.base_ratio * self.height_total
        self.fin_height = (1 - self.base_ratio) * self.height_total

    @property
    def cross_section_area(self) -> float:
        """A_cross = L * H_b + n * w_f * H_f [mm^2]."""
        return self.base_width * self.base_height + self.n_fins * self.fin_width * self.fin_height


def is_valid(cfg: HeatsinkConfig) -> bool:
    """Check manufacturability: fin_width >= 2mm, gap >= 2mm, n_fins >= 2."""
    return cfg.fin_width >= 2.0 and cfg.gap >= 2.0 and cfg.n_fins >= 2


# ---------------------------------------------------------------------------
# Sweep grid
# ---------------------------------------------------------------------------

# Parameter grid values (per design spec)
L_VALUES = [i * SOURCE_WIDTH for i in range(1, 11)]  # 4, 8, ..., 40 mm
PITCH_RATIOS = [0.25, 0.50, 0.75]
DUTY_CYCLES = [0.1, 0.25, 0.5]
BASE_RATIOS = [0.1, 0.25, 0.5, 0.75]


def build_sweep_grid() -> list[HeatsinkConfig]:
    """Generate all valid configs from the full parameter grid.

    Full factorial: 10 * 3 * 3 * 4 = 360 combinations.
    After filtering for manufacturability: ~150-200 valid configs.
    """
    configs = []
    for L, pr, D, rb in product(L_VALUES, PITCH_RATIOS, DUTY_CYCLES, BASE_RATIOS):
        pitch = pr * L
        cfg = HeatsinkConfig(base_width=L, pitch=pitch, duty_cycle=D, base_ratio=rb)
        if is_valid(cfg):
            configs.append(cfg)
    return configs


# ---------------------------------------------------------------------------
# Geometry + FEMM problem builder
# ---------------------------------------------------------------------------

def _contact_position(cfg: HeatsinkConfig) -> tuple[float, float]:
    """Return (cx0, cx1) for the contact patch based on contact_mode."""
    if cfg.contact_mode == "centered":
        cx0 = (cfg.base_width - cfg.contact_width) / 2
    elif cfg.contact_mode == "single_fin":
        centers = [(i + 0.5) * cfg.pitch_actual for i in range(cfg.n_fins)]
        nearest = min(centers, key=lambda c: abs(c - cfg.base_width / 2))
        cx0 = nearest - cfg.contact_width / 2
    elif cfg.contact_mode == "between_fins":
        centers = sorted(
            [(i + 0.5) * cfg.pitch_actual for i in range(cfg.n_fins)],
            key=lambda c: abs(c - cfg.base_width / 2),
        )
        mid = (centers[0] + centers[1]) / 2
        cx0 = mid - cfg.contact_width / 2
    else:
        raise ValueError(f"Unknown contact_mode: {cfg.contact_mode!r}")
    cx1 = cx0 + cfg.contact_width
    cx0 = max(0.0, cx0)
    cx1 = min(cfg.base_width, cx1)
    return cx0, cx1


def _build_outline_nodes(cfg: HeatsinkConfig) -> list[Node]:
    """Build closed polygon nodes for the heatsink cross-section.

    Fins are centered within their period -- fin i center is at
    (i + 0.5) * pitch_actual. This gives equal gap/2 at each edge.
    """
    cx0, cx1 = _contact_position(cfg)
    H_b = cfg.base_height
    H_f = cfg.fin_height
    L = cfg.base_width

    # Bottom edge + right wall up to base height (clockwise from origin)
    nodes = [
        Node(0, 0),
        Node(cx0, 0),
        Node(cx1, 0),
        Node(L, 0),
        Node(L, H_b),
    ]

    # Fin zigzag: right to left
    for i in range(cfg.n_fins - 1, -1, -1):
        center_x = (i + 0.5) * cfg.pitch_actual
        left_x = center_x - cfg.fin_width / 2
        right_x = center_x + cfg.fin_width / 2
        nodes.extend([
            Node(right_x, H_b),
            Node(right_x, H_b + H_f),
            Node(left_x, H_b + H_f),
            Node(left_x, H_b),
        ])

    # Left wall back to origin
    nodes.append(Node(0, H_b))

    # Deduplicate consecutive nodes
    deduped = [nodes[0]]
    for n in nodes[1:]:
        if abs(n.x - deduped[-1].x) > 1e-6 or abs(n.y - deduped[-1].y) > 1e-6:
            deduped.append(n)
    if (abs(deduped[-1].x - deduped[0].x) < 1e-6
            and abs(deduped[-1].y - deduped[0].y) < 1e-6):
        deduped.pop()

    return deduped


def build_femm_problem(cfg: HeatsinkConfig) -> str:
    """Build complete FEMM heat flow problem from config, return Lua script."""
    nodes = _build_outline_nodes(cfg)
    cx0, cx1 = _contact_position(cfg)

    # Geometry
    geo = Geometry()
    geo.nodes = list(nodes)
    geo.lines = [Line(nodes[i], nodes[(i + 1) % len(nodes)]) for i in range(len(nodes))]

    # FEMM problem
    qs = P / (cfg.contact_width * DEPTH * 1e-6)  # heat flux [W/m^2]

    problem = FemmProblem(out_file="heatsink_data.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS, type="planar",
        precision=1e-8, depth=DEPTH, minangle=30,
    )
    problem.create_geometry(geo)

    # Material
    aluminum = HeatFlowMaterial(material_name="Aluminum", kx=200.0, ky=200.0, qv=0.0, kt=0.0)
    problem.add_material(aluminum)
    problem.define_block_label(Node(cfg.base_width / 2, cfg.base_height / 2), aluminum)

    # Boundary conditions
    heat_source = HeatFlowHeatFlux(name="HeatSource", qs=-qs)
    heat_source.Tset = 0
    heat_source.Tinf = 0
    heat_source.h = 0
    heat_source.beta = 0
    problem.add_boundary(heat_source)

    convection = HeatFlowConvection(name="AirConvection", Tinf=T_AMB, h=H_CONV)
    convection.Tset = 0
    convection.qs = 0
    convection.beta = 0
    problem.add_boundary(convection)

    # Assign BCs -- find the contact segment by its midpoint x
    contact_mid_x = (cx0 + cx1) / 2
    for i in range(len(nodes)):
        seg = Line(nodes[i], nodes[(i + 1) % len(nodes)])
        mid = seg.selection_point()
        if abs(mid.y) < 1e-6 and abs(mid.x - contact_mid_x) < 1e-3:
            problem.set_boundary_definition_segment(mid, heat_source, elementsize=1)
        elif abs(seg.start_pt.y) < 1e-6 and abs(seg.end_pt.y) < 1e-6:
            pass  # bottom segment -- insulated
        else:
            problem.set_boundary_definition_segment(mid, convection, elementsize=1)

    # Analysis
    problem.make_analysis("planar")

    # Post-processing: extract metrics
    contact_center_x = (cx0 + cx1) / 2
    outermost_fin_tip_x = 0.5 * cfg.pitch_actual  # leftmost fin center

    problem.lua_script.append(f"T_max = ho_getpointvalues({contact_center_x}, 0)")
    problem.lua_script.append(
        f"T_min = ho_getpointvalues({outermost_fin_tip_x}, "
        f"{cfg.base_height + cfg.fin_height})"
    )

    problem.lua_script.append(f"ho_selectblock({cfg.base_width / 2}, {cfg.base_height / 2})")
    problem.lua_script.append("avg_T = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")

    problem.lua_script.append('write(file_out, "AverageTemperature_K = ", avg_T, "\\n")')
    problem.lua_script.append('write(file_out, "T_max_K = ", T_max, "\\n")')
    problem.lua_script.append('write(file_out, "T_min_K = ", T_min, "\\n")')

    problem.close()
    return "\n".join(problem.lua_script)
