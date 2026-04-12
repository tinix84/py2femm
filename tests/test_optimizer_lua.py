"""Tests for the optimizer's Lua generation — no FEMM needed."""

from heatsink_optimize import (
    OptimConfig, ChipConfig, HeatsinkConfig, build_model,
)


def test_build_model_produces_valid_lua():
    """build_model() should produce Lua without table indexing syntax."""
    cfg = OptimConfig(
        chip_a=ChipConfig(name="ChipA", power=5.0),
        chip_b=ChipConfig(name="ChipB", power=15.0),
        heatsink=HeatsinkConfig(base_w=100.0, base_h=100.0, base_t=5.0),
    )
    lua = build_model(cfg, x_a=30.0, y_a=0.0, x_b=70.0, y_b=0.0)

    # Must contain ho_getpointvalues calls
    assert "ho_getpointvalues" in lua

    # Must NOT use table indexing T_A[1] — FEMM Lua 4.0 returns multiple values
    assert "[1]" not in lua

    # Must write temperature values to file_out
    assert "T_A_K" in lua
    assert "T_B_K" in lua

    # Must have PY2FEMM_DONE sentinel (from close())
    assert "PY2FEMM_DONE" in lua

    # Must end with quit()
    lines = lua.strip().splitlines()
    assert lines[-1].strip() == "quit()"
