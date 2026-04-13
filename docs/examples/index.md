# All Examples

Complete list of examples included in the `examples/` directory, organized by physics type.

---

## Heat Flow

| Example | File | Description |
|---------|------|-------------|
| [Heat Sink Tutorial](heatsink-baseline.md) | `heatflow/heatsink/heatsink_tutorial.py` | Full interactive tutorial: 5-fin heat sink, 10W source, validation against FEMM Tutorial #7 |
| Heat Sink (library) | `heatflow/heatsink/heatsink.py` | Standalone heat sink builder function, used by notebooks |
| [Heat Sink Parametric](heatsink-parametric.md) | `heatflow/heatsink/heatsink_parametric.py` | Square-wave parametrization, 360-config factorial sweep |
| [Chip Placement Optimization](optimization.md) | `heatflow/heatsink/heatsink_optimize.py` | 2-chip placement optimizer with brute-force grid + Nelder-Mead |
| Heat Sink Baseline Notebook | `heatflow/heatsink/heatsink_baseline.ipynb` | Jupyter notebook: baseline analysis with fixed BCs and bitmap |
| Heat Sink Parametric Notebook | `heatflow/heatsink/heatsink_parametric.ipynb` | Jupyter notebook: full parametric sweep with visualizations |
| Heat Sink Optimization Notebook | `heatflow/heatsink/heatsink_optimize.ipynb` | Jupyter notebook: 2-chip placement optimization |
| Simple Thermal | `01_simple_thermal.py` | Minimal thermal example |

---

## Electrostatics

| Example | File | Description |
|---------|------|-------------|
| Planar Capacitor | `electrostatics/capacitance/planar_capacitor.py` | Parallel plate capacitor: geometry, solve, extract capacitance |
| Capacitor E2E | `02_e2e_capacitor_with_plot.py` | End-to-end capacitor example with result plotting |
| Double-L Shape | `electrostatics/double_l_shape/double_l_shape_domain.py` | Complex electrode geometry |

---

## Magnetics

| Example | File | Description |
|---------|------|-------------|
| Solenoid | `magnetics/solenoid/` | Solenoid coil analysis |
| SynRM | `SynRM/` | Synchronous reluctance machine from DXF import |
| FI-PMASynRM | `magnetics/FI-PMASynRM/` | Flux-intensifying PMA-SynRM: cogging torque, average torque, NSGA-II optimization |
| ISPMSM | `magnetics/ISPMSM/` | Interior surface PM synchronous machine |
| PMDC Motor | `magnetics/PMDC_motor/` | Permanent magnet DC motor |
| Reluctance Machine | `magnetics/reluctance_machine/` | Switched reluctance machine |
| Toyota Prius | `magnetics/toyota_prius/` | Toyota Prius IPM motor benchmark |
| Mesh Extract | `magnetics/MeshExtract.py` | Extract and analyze FEMM mesh topology |

---

## Running examples

Most examples can be run directly:

```bash
python examples/heatflow/heatsink/heatsink_tutorial.py --start-server
```

For notebook examples:

```bash
jupyter notebook examples/heatflow/heatsink/heatsink_baseline.ipynb
```

All examples that submit to FEMM require the py2femm server to be running. See [Server Setup](../getting-started/server.md).
