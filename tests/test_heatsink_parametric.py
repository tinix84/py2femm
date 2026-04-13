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
