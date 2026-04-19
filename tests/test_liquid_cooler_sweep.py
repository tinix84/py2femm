from __future__ import annotations
import csv
import io
import pytest

from examples.heatflow.liquid_cooler_to247.config import default_waffler_config
from examples.heatflow.liquid_cooler_to247.sweep import (
    parse_csv_result,
    compute_coupling_matrix,
    run_sweep,
)


def _make_mock_result(n_devices: int, t_j_values: list[float], t_h: float = 365.0) -> str:
    lines = [f"T_j_{i} = {t_j_values[i]}\n" for i in range(n_devices)]
    lines += [f"T_case_{i} = {t_j_values[i] - 1.0}\n" for i in range(n_devices)]
    lines.append(f"T_h_surface = {t_h}\n")
    return "".join(lines)


def test_parse_csv_result_extracts_t_j():
    raw = _make_mock_result(2, [390.0, 385.0])
    result = parse_csv_result(raw, n_devices=2)
    assert result["T_j_0"] == pytest.approx(390.0)
    assert result["T_j_1"] == pytest.approx(385.0)


def test_parse_csv_result_extracts_t_h_surface():
    raw = _make_mock_result(1, [388.0], t_h=366.0)
    result = parse_csv_result(raw, n_devices=1)
    assert result["T_h_surface"] == pytest.approx(366.0)


def test_compute_coupling_matrix_shape():
    cfg = default_waffler_config(n_devices=2, p_loss=30.0)

    def fake_run(problem):
        return _make_mock_result(2, [380.0, 370.0])

    C = compute_coupling_matrix(cfg, builder="circular", run_fn=fake_run)
    assert C.shape == (2, 2)


def test_compute_coupling_matrix_diagonal_dominance():
    cfg = default_waffler_config(n_devices=2, p_loss=30.0)

    call_count = [0]

    def fake_run(problem):
        i = call_count[0]
        call_count[0] += 1
        if i == 0:
            return _make_mock_result(2, [395.0, 368.0])
        return _make_mock_result(2, [366.0, 393.0])

    C = compute_coupling_matrix(cfg, builder="circular", run_fn=fake_run)
    assert C[0, 0] > C[0, 1]
    assert C[1, 1] > C[1, 0]


def test_run_sweep_csv_has_required_columns():
    cfg = default_waffler_config(n_devices=1, p_loss=30.0)

    def fake_run(problem):
        return _make_mock_result(1, [390.0])

    buf = io.StringIO()
    run_sweep(
        cfg=cfg,
        builders=["circular"],
        p_loss_values=[30.0],
        run_fn=fake_run,
        out=buf,
    )
    buf.seek(0)
    reader = csv.DictReader(buf)
    row = next(reader)
    assert "builder" in row
    assert "n_devices" in row
    assert "p_loss" in row
    assert "T_j_0" in row
    assert "T_h_surface" in row
    assert "Rth_j_inlet_0" in row
