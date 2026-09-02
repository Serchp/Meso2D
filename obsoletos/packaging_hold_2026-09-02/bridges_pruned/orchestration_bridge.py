from src.simulation.orchestration_EN import SimulationController as _SimulationControllerEN


class SimulationController(_SimulationControllerEN):
    """Unified bridge controller.

    Current implementation delegates to the EN controller while the window
    exposes compatibility aliases for legacy ES names.
    """

    pass
