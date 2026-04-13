# Installation

py2femm requires Python 3.10+ and FEMM 4.2. The simulation engine (FEMM) runs only on Windows, but the Python client can run on any platform that connects to a py2femm server.

---

## 1. Install FEMM 4.2 (Windows)

Download and install [FEMM 4.2](https://www.femm.info/wiki/Download) to the default location:

```
C:\femm42\
```

Verify the binary exists at `C:\femm42\bin\femm.exe`.

---

## 2. Install py2femm

### Core library (script generation + client)

```bash
pip install -e .
```

### With REST server dependencies

```bash
pip install -e ".[server]"
```

### Everything (server + dev tools + docs)

```bash
pip install -e ".[all]"
```

### Interactive setup on Windows

```bat
setup_femm.bat
```

This creates `config/default.yml` with your Python environment and FEMM path.

---

## 3. Platform-specific notes

### Windows (native)

The simplest setup. Install FEMM 4.2 and py2femm, then start the server.

### Linux / WSL

FEMM does not run natively on Linux. Two options:

1. **WSL with Windows host** -- run the py2femm server on Windows, connect from WSL via REST API. The client auto-detects WSL when `/mnt/c/` exists.
2. **Wine** -- install FEMM under Wine. This is experimental and not officially supported.

### Docker

!!! note "Coming soon"
    A Docker image with Wine + FEMM pre-installed is planned. For now, run the server on a Windows host and connect remotely.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | >= 2.0 | Data validation and settings |
| `pyyaml` | >= 6.0 | Configuration file parsing |
| `click` | >= 8.0 | CLI interface |
| `pandas` | >= 1.5 | Result handling and parametric sweeps |
| `httpx` | >= 0.24 | HTTP client for REST API |
| `fastapi` | >= 0.100 | REST server (optional, `server` extra) |
| `uvicorn` | >= 0.20 | ASGI server (optional, `server` extra) |
| `numpy` | -- | Geometry and numerical operations |
| `matplotlib` | -- | Plotting (used by examples) |

---

## Verify installation

```bash
# Check CLI is available
py2femm --help

# Check server health (requires running server)
py2femm status
```

See [Server Setup](server.md) for launching the REST server, or jump to the [Quick Start](quickstart.md) to run your first simulation.
