from __future__ import annotations
import pytest
from examples.heatflow.liquid_cooler_to247.config import default_waffler_config
from examples.heatflow.liquid_cooler_to247.rectangular import build_rectangular


@pytest.fixture
def lua_1dev():
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)
    return "\n".join(build_rectangular(cfg).lua_script)


@pytest.fixture
def lua_3dev():
    cfg = default_waffler_config(n_devices=3, p_loss=30.0)
    return "\n".join(build_rectangular(cfg).lua_script)


def test_returns_femm_problem():
    from py2femm.femm_problem import FemmProblem
    cfg = default_waffler_config(n_devices=1)
    assert isinstance(build_rectangular(cfg), FemmProblem)


def test_no_circle_arcs(lua_1dev):
    assert "hi_addarc" not in lua_1dev


def test_aluminum_material_defined(lua_1dev):
    assert "Aluminum" in lua_1dev
    assert "160" in lua_1dev


def test_silicon_material_defined(lua_1dev):
    assert "Silicon" in lua_1dev


def test_copper_material_defined(lua_1dev):
    assert "Copper" in lua_1dev


def test_convection_bc_on_channel_walls(lua_1dev):
    assert "CoolantConvection" in lua_1dev


def test_heat_flux_bc_per_device(lua_3dev):
    assert "HeatFlux_0" in lua_3dev
    assert "HeatFlux_1" in lua_3dev
    assert "HeatFlux_2" in lua_3dev


def test_post_processing_all_devices(lua_3dev):
    assert "T_j_0" in lua_3dev
    assert "T_j_1" in lua_3dev
    assert "T_j_2" in lua_3dev


def test_t_h_surface_in_output(lua_1dev):
    assert "T_h_surface" in lua_1dev
    assert "ho_blockintegral(0)" in lua_1dev


def test_planar_problem(lua_1dev):
    assert "planar" in lua_1dev


def test_no_ho_reload(lua_1dev):
    assert "ho_reload" not in lua_1dev
