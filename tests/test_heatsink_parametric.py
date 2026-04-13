"""Tests for heatsink_parametric — no FEMM server needed."""

from heatsink_parametric import HeatsinkConfig, is_valid, build_sweep_grid


class TestHeatsinkConfig:
    def test_derived_quantities_basic(self):
        """L=20mm, pitch=10mm → n=2, p_actual=10, w_f=D*10, etc."""
        cfg = HeatsinkConfig(base_width=20.0, pitch=10.0, duty_cycle=0.5, base_ratio=0.25)
        assert cfg.n_fins == 2
        assert cfg.pitch_actual == 10.0
        assert cfg.fin_width == 5.0  # 0.5 * 10
        assert cfg.gap == 5.0  # (1-0.5) * 10
        assert cfg.base_height == 6.25  # 0.25 * 25
        assert cfg.fin_height == 18.75  # (1-0.25) * 25

    def test_n_fins_minimum_two(self):
        """n_fins is always >= 2 even with large pitch."""
        cfg = HeatsinkConfig(base_width=4.0, pitch=100.0, duty_cycle=0.5, base_ratio=0.5)
        assert cfg.n_fins == 2

    def test_pitch_actual_fills_width(self):
        """Actual pitch adjusts so n*p_actual == L exactly."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=15.0, duty_cycle=0.25, base_ratio=0.25)
        # round(40/15) = 3 fins → p_actual = 40/3 ≈ 13.333
        assert cfg.n_fins == 3
        assert abs(cfg.n_fins * cfg.pitch_actual - 40.0) < 1e-10

    def test_cross_section_area(self):
        """A_cross = L * H_b + n * w_f * H_f."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        # n=4, p=10, w_f=2.5, g=7.5, H_b=6.25, H_f=18.75
        # A = 40*6.25 + 4*2.5*18.75 = 250 + 187.5 = 437.5
        assert cfg.cross_section_area == 437.5


class TestIsValid:
    def test_valid_config(self):
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        # n=4, p=10, w_f=2.5, g=7.5 → all valid
        assert is_valid(cfg)

    def test_fin_too_narrow(self):
        """w_f < 2mm → invalid."""
        cfg = HeatsinkConfig(base_width=20.0, pitch=10.0, duty_cycle=0.1, base_ratio=0.25)
        # w_f = 0.1 * 10 = 1.0 < 2
        assert not is_valid(cfg)

    def test_gap_too_narrow(self):
        """gap < 2mm → invalid."""
        # w_f=4.0, g=1.0 < 2 → invalid
        cfg2 = HeatsinkConfig(base_width=20.0, pitch=5.0, duty_cycle=0.8, base_ratio=0.25)
        assert not is_valid(cfg2)

    def test_only_one_fin(self):
        """n_fins < 2 would be invalid, but __post_init__ clamps to 2."""
        cfg = HeatsinkConfig(base_width=4.0, pitch=100.0, duty_cycle=0.5, base_ratio=0.5)
        assert cfg.n_fins == 2  # clamped


class TestBuildSweepGrid:
    def test_all_configs_are_valid(self):
        configs = build_sweep_grid()
        for cfg in configs:
            assert is_valid(cfg), f"Invalid config in grid: {cfg}"

    def test_grid_count_reasonable(self):
        """Spec estimates 150-200 valid configs from 360 total."""
        configs = build_sweep_grid()
        assert 100 <= len(configs) <= 300, f"Got {len(configs)} valid configs"

    def test_all_L_values_present(self):
        """Most L values should have at least some valid configs."""
        configs = build_sweep_grid()
        L_values = {cfg.base_width for cfg in configs}
        # Small L values (4, 8) may have 0 valid configs, that's OK
        assert len(L_values) >= 6, f"Only {len(L_values)} distinct L values"


from heatsink_parametric import build_femm_problem


class TestBuildFemmProblem:
    def test_produces_valid_lua(self):
        """Lua script has required commands and no table indexing."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        lua = build_femm_problem(cfg)

        # Must be heat flow problem
        assert "hi_probdef" in lua
        assert '"millimeters"' in lua
        assert '"planar"' in lua

        # Must have geometry
        assert "hi_addnode" in lua
        assert "hi_addsegment" in lua

        # Must have material
        assert "Aluminum" in lua

        # Must extract T_avg, T_max, T_min
        assert "ho_blockintegral(0)" in lua
        assert "ho_getpointvalues" in lua
        assert "AverageTemperature_K" in lua
        assert "T_max_K" in lua
        assert "T_min_K" in lua

        # Must end with quit()
        assert lua.strip().splitlines()[-1].strip() == "quit()"

        # No table indexing (FEMM Lua 4.0)
        assert "[1]" not in lua

    def test_contact_patch_centered(self):
        """Contact patch nodes should be centered on base bottom."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        lua = build_femm_problem(cfg)

        # Contact patch: centered at L/2=20, width=4 → cx0=18, cx1=22
        assert "hi_addnode(18.0, 0)" in lua
        assert "hi_addnode(22.0, 0)" in lua

    def test_bottom_segments_insulated(self):
        """No convection BC on bottom segments (y=0, non-contact)."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=10.0, duty_cycle=0.25, base_ratio=0.25)
        lua = build_femm_problem(cfg)

        select_calls = [l for l in lua.splitlines() if "hi_selectsegment" in l]
        y0_selects = []
        for call in select_calls:
            inner = call.split("(")[1].split(")")[0]
            parts = inner.split(",")
            y_val = float(parts[1].strip())
            if abs(y_val) < 1e-6:
                y0_selects.append(call)

        # Only the contact patch midpoint should be selected at y=0
        assert len(y0_selects) == 1, f"Expected 1, got {len(y0_selects)}: {y0_selects}"

    def test_correct_number_of_fins(self):
        """Geometry should have correct fin nodes."""
        cfg = HeatsinkConfig(base_width=40.0, pitch=20.0, duty_cycle=0.5, base_ratio=0.25)
        # n=2, p=20, w_f=10, g=10, H_b=6.25, H_f=18.75, H_total=25
        lua = build_femm_problem(cfg)

        # Fin top nodes at y = H_b + H_f = 25.0
        fin_top_nodes = [l for l in lua.splitlines()
                         if "hi_addnode" in l and ", 25.0)" in l]
        # 2 fins × 2 top corners each = 4 nodes at y=25
        assert len(fin_top_nodes) == 4, f"Expected 4 fin top nodes, got {len(fin_top_nodes)}"
