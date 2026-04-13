# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `CONTRIBUTING.md`, `CHANGELOG.md`, architecture docs, and PRD

## [0.2.0] - 2026-04-13

### Added
- Heatsink parametric study module with square-wave fin parametrization
  (`HeatsinkConfig` dataclass, `build_sweep_grid`, `run_sweep` engine)
- Full factorial sweep over 360 configurations (base_width, pitch, duty_cycle,
  base_ratio) with automatic validity filtering
- Five parametric plotting functions: 1D sensitivity, 2D heatmap, scaling plot,
  contact-mode comparison, geometry overlay
- `heatsink_baseline.ipynb` notebook reproducing FEMM Tutorial #7 with fixed
  boundary conditions and FEMM bitmap capture
- `heatsink_parametric.ipynb` notebook for interactive full-factorial sweep
- FEMM bitmap capture (`ho_savebitmap`) and raw Lua `ho_getpointvalues` support
- 2-chip thermal optimizer example using scipy Nelder-Mead and brute-force grid
  (`heatsink_optimize.ipynb`)
- `conftest.py` for example imports in the test suite
- `PY2FEMM_DONE` sentinel in `FemmProblem.close()` for reliable job completion
  detection

### Fixed
- Bottom segments now insulated (skip convection BC where both endpoints have
  y=0 and segment is not the contact patch) -- T_avg matches FEMM Tutorial #7
  at ~356 K instead of ~334 K
- Executor rewritten to use file-polling instead of `proc.communicate()`,
  fixing hangs on large Lua outputs
- Removed Lua table indexing from optimizer `ho_getpointvalues` calls
- Hardened plot functions against empty input and variable mode count
- DEVNULL for executor subprocess pipes to prevent buffer deadlocks

### Changed
- Parametric sweep removed from `heatsink_tutorial.py` (superseded by dedicated
  parametric module)

## [0.1.0] - 2026-04-05

### Added
- Initial release: py2femm Phase 1 MVP
- Client library (`py2femm/`) with `FemmProblem` Lua script generator
- Support for 4 physics: magnetics, electrostatics, heat flow, current flow
  (2D planar and axisymmetric)
- Geometry primitives: `Node`, `Line`, `CircleArc`, `Geometry` with transform
  operations (rotate, mirror, translate)
- Physics-specific materials and boundary conditions with `__str__` Lua
  generation
- REST server (`py2femm_server/`) with FastAPI endpoints for job submission,
  status, and health checks
- FEMM subprocess executor with Lua preamble injection and timeout handling
- In-memory job store with lifecycle tracking (queued -> running -> completed |
  failed)
- Auto-detecting client (`FemmClient`) with local (shared filesystem) and
  remote (REST API) modes
- Filesystem watcher for shared-filesystem bridge mode (WSL /mnt/c/)
- CLI with `run`, `run-batch`, and `status` commands
- Heat sink tutorial example (`examples/heatflow/heatsink/`)
- Simple thermal and capacitor end-to-end examples
- `setup_femm.bat` for Windows environment setup
- `start_femm_server.bat` for launching the REST server
- Test suite covering geometry, materials, BCs, client, server, and executor

[Unreleased]: https://github.com/tinix84/py2femm/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/tinix84/py2femm/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/tinix84/py2femm/releases/tag/v0.1.0
