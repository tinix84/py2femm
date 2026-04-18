from __future__ import annotations
import math
import pytest
from examples.heatflow.liquid_cooler_to247.config import (
    DeviceConfig, LiquidCoolerConfig, compute_h, default_waffler_config,
)


def test_default_waffler_config_device_count():
    cfg = default_waffler_config(n_devices=3)
    assert cfg.n_devices == 3


def test_default_waffler_config_single_device():
    cfg = default_waffler_config(n_devices=1)
    assert cfg.n_devices == 1


def test_b_cp_equals_n_devices_times_pitch():
    cfg = default_waffler_config(n_devices=3)
    assert math.isclose(cfg.b_cp, cfg.n_devices * cfg.device_pitch, rel_tol=1e-9)


def test_device_pitch_equals_bp_w_plus_spacing():
    cfg = default_waffler_config(n_devices=2)
    assert math.isclose(cfg.device_pitch, cfg.devices[0].bp_w + cfg.device_spacing, rel_tol=1e-9)


def test_n_channels_covers_full_width():
    cfg = default_waffler_config(n_devices=3)
    assert cfg.n_channels * cfg.s_t >= cfg.b_cp


def test_compute_h_returns_float():
    cfg = default_waffler_config(n_devices=1)
    h = compute_h(cfg)
    assert isinstance(h, float)


def test_compute_h_waffler_defaults_reasonable_range():
    cfg = default_waffler_config(n_devices=1)
    h = compute_h(cfg)
    assert 5_000 < h < 20_000, f"h={h:.0f} W/m²K out of expected range"


def test_compute_h_custom_dh():
    cfg = default_waffler_config(n_devices=1)
    h_circ = compute_h(cfg)
    h_rect = compute_h(cfg, dh_mm=3.0)
    assert h_circ != h_rect


def test_waffler_config_geometry_defaults():
    cfg = default_waffler_config()
    assert cfg.h_cp == pytest.approx(4.0)
    assert cfg.d_t == pytest.approx(2.0)
    assert cfg.s_t == pytest.approx(6.0)
    assert cfg.t_inlet == pytest.approx(363.15)
