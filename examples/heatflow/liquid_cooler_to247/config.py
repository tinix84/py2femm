from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class DeviceConfig:
    name: str
    p_loss: float        # W — power dissipated by this device
    a_si: float = 5.0   # mm — Si die side length (square)
    bp_w: float = 15.0  # mm — Cu baseplate width
    h_cu: float = 3.0   # mm — Cu baseplate height
    d_tim: float = 0.2  # mm — TIM thickness
    k_tim: float = 2.0  # W/mK — TIM thermal conductivity


@dataclass
class LiquidCoolerConfig:
    devices: list[DeviceConfig]
    h_cp: float = 4.0           # mm — cooler block height
    d_t: float = 2.0            # mm — circular channel diameter
    s_t: float = 6.0            # mm — channel pitch
    ch_w: float = 3.0           # mm — rectangular channel width
    ch_h: float = 3.5           # mm — rectangular channel height
    fin_w: float = 1.0          # mm — fin wall width (rectangular channels)
    t_inlet: float = 363.15     # K  — coolant inlet temperature (90°C)
    m_dot: float = 0.0028       # kg/s — mass flow rate per channel
    l_cp: float = 30.0          # mm — cooler depth (extrusion into page)
    device_spacing: float = 3.0 # mm — gap between adjacent baseplates

    @property
    def n_devices(self) -> int:
        return len(self.devices)

    @property
    def device_pitch(self) -> float:
        return self.devices[0].bp_w + self.device_spacing

    @property
    def b_cp(self) -> float:
        return self.n_devices * self.device_pitch

    @property
    def n_channels(self) -> int:
        return math.ceil(self.b_cp / self.s_t)

    def __post_init__(self) -> None:
        if not self.devices:
            raise ValueError("LiquidCoolerConfig requires at least one device")
        bp_ws = {dev.bp_w for dev in self.devices}
        if len(bp_ws) > 1:
            raise ValueError(f"All devices must have the same bp_w; got {bp_ws}")


_WATER_90C = {
    "lam": 0.674,
    "cp": 4205.0,
    "eta": 0.32e-3,
}


def compute_h(cfg: LiquidCoolerConfig, dh_mm: float | None = None) -> float:
    """Convective coefficient [W/m²K] on channel wall — Waffler eq. 4.145-4.148."""
    dh = (dh_mm if dh_mm is not None else cfg.d_t) * 1e-3
    length = cfg.l_cp * 1e-3
    eta = _WATER_90C["eta"]
    lam = _WATER_90C["lam"]
    Pr = eta * _WATER_90C["cp"] / lam
    Re = 4 * cfg.m_dot / (math.pi * eta * dh)

    if Re <= 2300:
        Nu = (3.657**3 + 0.644**3 * (Pr * Re * dh / length) ** 1.5) ** (1 / 3)
    else:
        # Gnielinski (1976) — valid for Re > 2300
        zeta = 1.0 / (0.78 * math.log(Re) - 1.5) ** 2  # friction factor (Petukhov 1970)
        Nu = (zeta / 8.0 * (Re - 1000.0) * Pr) / (
            1.0 + 12.7 * math.sqrt(zeta / 8.0) * (Pr ** (2.0 / 3.0) - 1.0)
        )

    return Nu * lam / dh


def default_waffler_config(n_devices: int = 3, p_loss: float = 30.0) -> LiquidCoolerConfig:
    """Config reproducing Waffler §4.4.2 geometry with n TO-247 devices."""
    devices = [DeviceConfig(name=f"D{i}", p_loss=p_loss) for i in range(n_devices)]
    return LiquidCoolerConfig(
        devices=devices,
        h_cp=4.0,
        d_t=2.0,
        s_t=6.0,
        ch_w=3.0,
        ch_h=3.5,
        fin_w=1.0,
        t_inlet=363.15,
        m_dot=0.0028,
        l_cp=30.0,
        device_spacing=3.0,
    )
