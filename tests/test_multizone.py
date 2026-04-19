"""Unit tests for multi-zone heatsink model (no FEMM required)."""
from __future__ import annotations

import pytest
from heatsink_multizone import Zone, Chip, MultiZoneConfig, validate_config


def test_valid_config():
    """A well-formed 3-zone 2-chip config passes validation."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=60, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=60, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=5),
            Zone(x_start=100, x_end=180, material="Copper", kx=385, ky=385, h_conv=50),
        ],
        chips=[
            Chip(name="ChipA", x_center=30, width=20, power=5.0),
            Chip(name="ChipB", x_center=140, width=30, power=15.0),
        ],
        base_w=180, base_h=10,
    )
    validate_config(cfg)  # should not raise


def test_zones_gap_rejected():
    """Zones with a gap between them should fail validation."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=50, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=60, x_end=180, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=30, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="contiguous"):
        validate_config(cfg)


def test_zones_wrong_start_rejected():
    """First zone must start at 0."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=10, x_end=180, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=90, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="start at 0"):
        validate_config(cfg)


def test_zones_wrong_end_rejected():
    """Last zone must end at base_w."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=50, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="end at base_w"):
        validate_config(cfg)


def test_chip_outside_base_rejected():
    """Chip contact extending beyond base_w should fail."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=180, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=175, width=20, power=5.0)],
        base_w=180, base_h=10,
    )
    with pytest.raises(ValueError, match="outside"):
        validate_config(cfg)


from heatsink_multizone import build_geometry, build_model


def _make_3zone_2chip_config() -> MultiZoneConfig:
    """Standard 3-zone 2-chip config for tests."""
    return MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=60, material="Aluminum", kx=200, ky=200, h_conv=15),
            Zone(x_start=60, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=5),
            Zone(x_start=100, x_end=180, material="Copper", kx=385, ky=385, h_conv=50),
        ],
        chips=[
            Chip(name="ChipA", x_center=30, width=20, power=5.0),
            Chip(name="ChipB", x_center=140, width=30, power=15.0),
        ],
        base_w=180, base_h=10,
    )


def test_geometry_node_count():
    """3 zones + 2 chips: expect correct node count."""
    cfg = _make_3zone_2chip_config()
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    # Bottom edge nodes: 0, 20, 40, 60, 100, 125, 155, 180 = 8 unique x-values
    # Top edge nodes: 0, 60, 100, 180 = 4 x-values at y=base_h
    # Total unique = 8 + 4 = 12
    assert len(geo.nodes) == 12


def test_geometry_internal_partition_count():
    """3 zones = 2 internal partition lines."""
    cfg = _make_3zone_2chip_config()
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    assert len(internal_lines) == 2


def test_geometry_top_segments_count():
    """3 zones = 3 top segments."""
    cfg = _make_3zone_2chip_config()
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    assert len(top_segments) == 3


def test_chip_at_zone_boundary_no_duplicate():
    """Chip edge coinciding with zone boundary should not create duplicate nodes."""
    cfg = MultiZoneConfig(
        zones=[
            Zone(x_start=0, x_end=50, material="Aluminum", kx=200, ky=200, h_conv=25),
            Zone(x_start=50, x_end=100, material="Aluminum", kx=200, ky=200, h_conv=25),
        ],
        chips=[Chip(name="ChipA", x_center=50, width=20, power=5.0)],
        base_w=100, base_h=10,
    )
    geo, bottom_nodes, top_segments, internal_lines = build_geometry(cfg)
    bottom_xs = sorted(set(round(n.x, 6) for n in bottom_nodes))
    assert len(bottom_xs) == len(bottom_nodes), "Duplicate bottom nodes detected"


def test_build_model_material_dedup():
    """Two zones with same material name should produce only one hi_addmaterial call."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    # Aluminum appears in zone 0 and 1, Copper in zone 2 → 2 hi_addmaterial calls
    assert lua.count("hi_addmaterial") == 2


def test_build_model_block_labels_per_zone():
    """Each zone gets its own hi_addblocklabel call."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert lua.count("hi_addblocklabel") == 3


def test_build_model_per_zone_convection():
    """Each zone's top segment gets a distinct convection BC."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    # 3 zones with different h values → 3 hi_addboundprop calls for convection
    # Plus 2 heat flux BCs for chips → total 5 hi_addboundprop
    assert lua.count("hi_addboundprop") == 5


def test_build_model_chip_heat_flux():
    """Each chip gets a heat flux BC."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "Heat_ChipA" in lua
    assert "Heat_ChipB" in lua


def test_build_model_no_table_indexing():
    """FEMM Lua 4.0: no table indexing [1] allowed."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "[1]" not in lua


def test_build_model_has_sentinel():
    """Lua must contain PY2FEMM_DONE sentinel."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "PY2FEMM_DONE" in lua


def test_build_model_ends_with_quit():
    """Lua must end with quit()."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    lines = lua.strip().splitlines()
    assert lines[-1].strip() == "quit()"


def test_build_model_writes_chip_temperatures():
    """Lua must write T_ChipA_K and T_ChipB_K to file_out."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "T_ChipA_K" in lua
    assert "T_ChipB_K" in lua


def test_build_model_writes_zone_temperatures():
    """Lua must write per-zone average temperatures."""
    cfg = _make_3zone_2chip_config()
    lua = build_model(cfg)
    assert "T_avg_zone_0_K" in lua
    assert "T_avg_zone_1_K" in lua
    assert "T_avg_zone_2_K" in lua
