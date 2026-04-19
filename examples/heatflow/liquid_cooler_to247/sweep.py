from __future__ import annotations

import csv
import re
import sys
from collections.abc import Callable

import numpy as np

from py2femm.femm_problem import FemmProblem

from .circular import build_circular
from .config import DeviceConfig, LiquidCoolerConfig, default_waffler_config
from .rectangular import build_rectangular

_BUILDERS = {"circular": build_circular, "rectangular": build_rectangular}


def parse_csv_result(raw: str, n_devices: int) -> dict[str, float]:
    """Parse FEMM CSV output lines into a flat dict of float values."""
    result: dict[str, float] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([\w]+)\s*=\s*([0-9eE+\-.]+)", line)
        if m:
            result[m.group(1)] = float(m.group(2))
    missing = [f"T_j_{i}" for i in range(n_devices) if f"T_j_{i}" not in result]
    if missing:
        raise ValueError(f"FEMM output missing keys: {missing}")
    return result


def _make_config(cfg: LiquidCoolerConfig, p_loss_per_device: list[float]) -> LiquidCoolerConfig:
    """Return a new config with per-device p_loss values replaced."""
    devices = [
        DeviceConfig(
            name=dev.name,
            p_loss=p,
            a_si=dev.a_si,
            bp_w=dev.bp_w,
            h_cu=dev.h_cu,
            d_tim=dev.d_tim,
            k_tim=dev.k_tim,
        )
        for dev, p in zip(cfg.devices, p_loss_per_device)
    ]
    return LiquidCoolerConfig(
        devices=devices,
        h_cp=cfg.h_cp,
        d_t=cfg.d_t,
        s_t=cfg.s_t,
        ch_w=cfg.ch_w,
        ch_h=cfg.ch_h,
        fin_w=cfg.fin_w,
        t_inlet=cfg.t_inlet,
        m_dot=cfg.m_dot,
        l_cp=cfg.l_cp,
        device_spacing=cfg.device_spacing,
    )


def compute_coupling_matrix(
    cfg: LiquidCoolerConfig,
    builder: str,
    run_fn: Callable[[FemmProblem], str],
) -> np.ndarray:
    """Return n×n coupling matrix C where C[k,i] = (T_j[i] - T_inlet) / P_k [K/W].

    Runs n_devices separate FEMM jobs with only one device powered at a time.
    """
    n = cfg.n_devices
    C = np.zeros((n, n))
    build_fn = _BUILDERS[builder]

    for k in range(n):
        p_losses = [cfg.devices[k].p_loss if i == k else 0.0 for i in range(n)]
        cfg_k = _make_config(cfg, p_losses)
        problem = build_fn(cfg_k)
        raw = run_fn(problem)
        parsed = parse_csv_result(raw, n_devices=n)
        p_k = cfg.devices[k].p_loss
        for i in range(n):
            t_j = parsed.get(f"T_j_{i}", cfg.t_inlet)
            C[k, i] = (t_j - cfg.t_inlet) / p_k if p_k > 0 else 0.0

    return C


def run_sweep(
    cfg: LiquidCoolerConfig,
    builders: list[str],
    p_loss_values: list[float],
    run_fn: Callable[[FemmProblem], str],
    out=None,
) -> None:
    """Run parametric sweep over builders × p_loss_values; write CSV to out."""
    if out is None:
        out = sys.stdout

    n = cfg.n_devices
    fieldnames = (
        ["builder", "n_devices", "p_loss", "T_h_surface"]
        + [f"T_j_{i}" for i in range(n)]
        + [f"T_case_{i}" for i in range(n)]
        + [f"Rth_j_inlet_{i}" for i in range(n)]
    )
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()

    for builder in builders:
        build_fn = _BUILDERS[builder]
        for p_loss in p_loss_values:
            cfg_run = _make_config(cfg, [p_loss] * n)
            problem = build_fn(cfg_run)
            raw = run_fn(problem)
            parsed = parse_csv_result(raw, n_devices=n)

            row: dict[str, object] = {
                "builder": builder,
                "n_devices": n,
                "p_loss": p_loss,
                "T_h_surface": parsed.get("T_h_surface", ""),
            }
            for i in range(n):
                t_j = parsed.get(f"T_j_{i}", "")
                row[f"T_j_{i}"] = t_j
                row[f"T_case_{i}"] = parsed.get(f"T_case_{i}", "")
                row[f"Rth_j_inlet_{i}"] = (
                    (float(t_j) - cfg.t_inlet) / p_loss if t_j and p_loss > 0 else ""
                )

            writer.writerow(row)


if __name__ == "__main__":
    from py2femm.client import FemmClient

    cfg = default_waffler_config(n_devices=3, p_loss=30.0)
    client = FemmClient()

    def _run(problem):
        result = client.run(problem)
        return result.csv_data or ""

    print("=== Coupling matrix (circular) ===")
    C = compute_coupling_matrix(cfg, builder="circular", run_fn=_run)
    print(C)

    print("\n=== Parametric sweep ===")
    with open("liquid_cooler_sweep.csv", "w", newline="") as f:
        run_sweep(
            cfg=cfg,
            builders=["circular", "rectangular"],
            p_loss_values=[10.0, 20.0, 30.0, 40.0, 50.0],
            run_fn=_run,
            out=f,
        )
    print("Results written to liquid_cooler_sweep.csv")
