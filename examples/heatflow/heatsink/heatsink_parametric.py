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
