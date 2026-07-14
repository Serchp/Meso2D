# Architecture

## Active entrypoint
- Run: `python Meso2D_refactor.py`
- This entrypoint now imports active modules from `src/`.

## Source layout
- `src/simulation/`
  - `orchestration.py`: `SimulationController`, `SimulationModel`, `create_worker`
- `src/workers/`
  - `Worker_clusters.py`, `Worker_elipses.py`, `Worker_poligonos.py`
- `src/io/`
  - `project.py`: project save/load helpers
- `src/visualization/`
  - `service.py`: viewport and current view image export
- `src/ui/`
  - `Main03.py`, `Main_inicio.py`, `dialog_GV.py`, `GV.py`

## Compatibility shims at project root
The following root files are kept as wrappers to avoid breaking old imports:
- `simulation_controller.py`
- `simulation_model.py`
- `simulation_service.py`
- `Worker_clusters.py`
- `Worker_elipses.py`
- `Worker_poligonos.py`
- `project_io.py`
- `visualization_service.py`
- `Main03.py`
- `Main_inicio.py`
- `dialog_GV.py`
- `GV.py`

## Legacy code
- Keep historical code in `obsoletos/`.
- Prefer editing only modules under `src/` for new changes.
