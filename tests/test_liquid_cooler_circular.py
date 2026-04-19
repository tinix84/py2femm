from __future__ import annotations
import pytest
from examples.heatflow.liquid_cooler_to247.config import default_waffler_config
from examples.heatflow.liquid_cooler_to247.circular import build_circular


@pytest.fixture
def lua_1dev():
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)
    return "\n".join(build_circular(cfg).lua_script)


@pytest.fixture
def lua_3dev():
    cfg = default_waffler_config(n_devices=3, p_loss=30.0)
    return "\n".join(build_circular(cfg).lua_script)


def test_returns_femm_problem():
    from py2femm.femm_problem import FemmProblem
    cfg = default_waffler_config(n_devices=1)
    assert isinstance(build_circular(cfg), FemmProblem)


def test_uses_circle_arcs(lua_1dev):
    assert "hi_addarc" in lua_1dev


def test_aluminum_material_defined(lua_1dev):
    assert "Aluminum" in lua_1dev
    assert "160" in lua_1dev


def test_silicon_material_defined(lua_1dev):
    assert "Silicon" in lua_1dev


def test_copper_material_defined(lua_1dev):
    assert "Copper" in lua_1dev


def test_convection_bc_defined(lua_1dev):
    assert "CoolantConvection" in lua_1dev


def test_heat_flux_bc_per_device_1dev(lua_1dev):
    assert "HeatFlux_0" in lua_1dev
    assert "HeatFlux_1" not in lua_1dev


def test_heat_flux_bc_per_device_3dev(lua_3dev):
    assert "HeatFlux_0" in lua_3dev
    assert "HeatFlux_1" in lua_3dev
    assert "HeatFlux_2" in lua_3dev


def test_arc_convection_raw_lua(lua_1dev):
    assert "hi_selectarcsegment" in lua_1dev
    assert "hi_setarcsegmentprop" in lua_1dev


def test_post_processing_t_j_per_device_1dev(lua_1dev):
    assert "T_j_0" in lua_1dev
    assert "ho_getpointvalues" in lua_1dev


def test_post_processing_t_j_per_device_3dev(lua_3dev):
    assert "T_j_0" in lua_3dev
    assert "T_j_1" in lua_3dev
    assert "T_j_2" in lua_3dev


def test_post_processing_t_h_surface(lua_1dev):
    assert "T_h_surface" in lua_1dev
    assert "ho_blockintegral(0)" in lua_1dev


def test_heat_flux_value_1dev():
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)
    lua = "\n".join(build_circular(cfg).lua_script)
    dev = cfg.devices[0]
    expected_qs = dev.p_loss / (dev.a_si * 1e-3 * cfg.l_cp * 1e-3)
    assert f"-{expected_qs:.4f}" in lua or str(int(-expected_qs)) in lua


def test_planar_problem_type(lua_1dev):
    assert "planar" in lua_1dev


def test_depth_in_lua(lua_1dev):
    cfg = default_waffler_config(n_devices=1)
    assert str(int(cfg.l_cp)) in lua_1dev
