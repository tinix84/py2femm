from __future__ import annotations

import os

import pytest
import requests

from examples.heatflow.liquid_cooler_to247.config import compute_h, default_waffler_config
from examples.heatflow.liquid_cooler_to247.circular import build_circular
from py2femm.client.auto import FemmClient

SERVER_URL = os.environ.get("PYFEMM_AGENT_URL", "http://localhost:8082")


def _server_available() -> bool:
    try:
        r = requests.get(f"{SERVER_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


skip_no_server = pytest.mark.skipif(
    not _server_available(),
    reason="FEMM server not available",
)


@skip_no_server
def test_waffler_single_device_circular():
    """Validate against Waffler §4.4 Table 4.17 targets:
    ΔT_h-i (total cooler) ≈ 4.55 K ± 10%
    """
    cfg = default_waffler_config(n_devices=1)
    problem = build_circular(cfg)

    client = FemmClient()
    result = client.run(problem)
    assert result.error is None, f"FEMM error: {result.error}"

    # Parse results
    lines = result.csv_data.strip().split("\n")
    data = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = float(v.strip())

    T_j = data["T_j_0"]
    T_h_surface = data["T_h_surface"]  # noqa: F841 — kept for diagnostics
    t_inlet = cfg.t_inlet
    p_loss = cfg.devices[0].p_loss

    delta_T_cooler = T_j - t_inlet  # total junction-to-inlet

    # Waffler §4.4 target: ΔT_h-i ≈ 4.55 K ± 10%
    assert 4.1 <= delta_T_cooler <= 5.0, (
        f"ΔT_j-inlet = {delta_T_cooler:.2f} K, expected 4.1–5.0 K (Waffler target: 4.55 K)"
    )

    # R_th,j-inlet sanity check (≈ 4.55/30 ≈ 0.152 K/W)
    R_th = delta_T_cooler / p_loss
    assert 0.12 <= R_th <= 0.18, f"R_th,j-inlet = {R_th:.4f} K/W, expected 0.12–0.18 K/W"


def test_waffler_h_analytical():
    """compute_h should return h matching Waffler §4.4 reference value.

    Waffler §4.4 reference: Re ≈ 5568, Gnielinski (1976) → h ≈ 9436 W/m²K.
    """
    cfg = default_waffler_config(n_devices=1)
    h = compute_h(cfg)
    assert 8500 <= h <= 10000, f"h = {h:.0f} W/m²K, expected 8500–10000 W/m²K (Waffler target: 9436 W/m²K)"
