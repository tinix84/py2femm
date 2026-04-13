# Server Setup

The py2femm REST server runs on Windows alongside FEMM 4.2. It receives Lua scripts over HTTP, executes them in FEMM, and returns results as CSV.

---

## Configuration file

The server reads configuration from `config/default.yml`:

```yaml
python:
  env_type: conda       # or venv
  env_name: my_env
  conda_root: C:\ProgramData\Anaconda3
femm:
  exe: C:\femm42\bin\femm.exe
```

Generate this file with the interactive setup:

```bat
setup_femm.bat
```

---

## Starting the server

### Windows batch file

```bat
start_femm_server.bat
```

### Manual start

```bash
python -m py2femm_server --host 0.0.0.0 --port 8082
```

### With FEMM window visible

```bash
python -m py2femm_server --host 0.0.0.0 --port 8082 --show-femm
```

This is useful for debugging -- you can see FEMM open, load the model, mesh, and solve in real time.

---

## Health check

Verify the server is running:

```bash
curl http://localhost:8082/api/v1/health
```

Expected response:

```json
{"status": "ok", "femm_exe": "C:\\femm42\\bin\\femm.exe"}
```

Or use the CLI:

```bash
py2femm status
```

---

## Client auto-detection

The `FemmClient` class auto-detects how to connect to the server. The detection order is:

| Priority | Condition | Mode |
|----------|-----------|------|
| 1 | Explicit `mode`/`url` arguments | As specified |
| 2 | `/mnt/c/` exists (WSL) | Local shared-filesystem |
| 3 | `PYFEMM_AGENT_URL` env var | Remote REST |
| 4 | `~/.py2femm/config.yml` with `agent.url` | Remote REST |
| 5 | None of the above | `ConnectionError` raised |

### Explicit connection

```python
from py2femm.client import FemmClient

# Remote mode (most common)
client = FemmClient(mode="remote", url="http://localhost:8082")

# Local mode (WSL only)
client = FemmClient(mode="local", workspace="/mnt/c/femm_workspace")
```

### Environment variable

```bash
export PYFEMM_AGENT_URL=http://192.168.1.100:8082
```

### Config file

Create `~/.py2femm/config.yml`:

```yaml
agent:
  url: http://192.168.1.100:8082
```

---

## Timeouts

The default timeout for `client.run()` is 300 seconds. For complex models or large parametric sweeps, increase it:

```python
result = client.run(lua_script, timeout=600)
```

!!! warning
    If a simulation hangs (e.g., FEMM fails to converge), the timeout will kill the subprocess. Check `result.error` for details.

---

## Error handling

```python
result = client.run(lua_script, timeout=120)

if result.error:
    print(f"Simulation failed: {result.error}")
else:
    print(f"Completed in {result.elapsed_s:.1f}s")
    print(result.csv_data)
```

The `ClientResult` dataclass contains:

| Field | Type | Description |
|-------|------|-------------|
| `csv_data` | `str | None` | Raw CSV output from FEMM |
| `error` | `str | None` | Error message if simulation failed |
| `elapsed_s` | `float` | Wall-clock time in seconds |
