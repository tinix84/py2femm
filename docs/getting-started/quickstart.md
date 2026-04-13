# Quick Start

Run your first FEMM simulation in 5 minutes. This guide walks through the heat sink baseline example end-to-end.

---

## Prerequisites

- Python 3.10+ installed
- FEMM 4.2 installed at `C:\femm42\`
- py2femm installed (`pip install -e ".[server]"`)

---

## Step 1 -- Start the server

Open a terminal on your Windows machine:

```bat
start_femm_server.bat
```

Or start manually:

```bash
python -m py2femm_server --host 0.0.0.0 --port 8082
```

Wait for the `Uvicorn running on http://0.0.0.0:8082` message.

!!! tip
    Add `--show-femm` to keep the FEMM window visible for debugging:
    ```bash
    python -m py2femm_server --host 0.0.0.0 --port 8082 --show-femm
    ```

---

## Step 2 -- Run the heat sink tutorial

In a second terminal:

```bash
python examples/heatflow/heatsink/heatsink_tutorial.py
```

Or let the script start the server automatically:

```bash
python examples/heatflow/heatsink/heatsink_tutorial.py --start-server
```

---

## Step 3 -- Check results

The script will print results like:

```
=== 6. Parse Results ===
  AverageTemperature_K = 356.2134
  T_contact_K = 382.4567
  T_base_K = 358.1234
  T_fintip_K = 312.5678

  Average temperature:  356.2 K  (83.1 C)
  Thermal resistance:   5.82 K/W
  Expected:             ~356 K,  R_th ~ 5.8 K/W
```

The average temperature of approximately 356 K and thermal resistance of approximately 5.8 K/W match the expected values from FEMM Tutorial #7.

---

## What just happened?

The tutorial script performed these steps:

1. **Defined dimensions** -- 5-fin aluminum heat sink, 35 mm wide, 100 mm deep
2. **Built geometry** -- closed polygon with 24 nodes and line segments
3. **Set up physics** -- aluminum material (k=200 W/m-K), heat flux BC on 4 mm contact, convection BC on all other surfaces
4. **Generated Lua** -- created a FEMM-compatible Lua script
5. **Submitted to FEMM** -- sent the script to the REST server
6. **Parsed results** -- extracted temperature and thermal resistance from CSV output

---

## What's next?

- [Heat Sink Tutorial](../examples/heatsink-baseline.md) -- detailed walkthrough of the same example
- [FemmProblem API](../guide/femm-problem.md) -- learn to build your own problems
- [Parametric Studies](../guide/parametric.md) -- sweep parameters across hundreds of configurations
- [Server Setup](server.md) -- advanced server configuration
