from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SimulationModel:
    sieve_size: Optional[List[int]] = None
    tpp: Optional[List[int]] = None
    x: Optional[float] = None
    y: Optional[float] = None
    Pagg: Optional[float] = None
    Pporos: Optional[float] = None
    dporo_min: Optional[float] = None
    dporo_max: Optional[float] = None
    r_react: Optional[float] = None
    dpto_max_aridos: Optional[float] = None
    dpto_min_aridos: Optional[float] = None
    dpto_max_pasta: Optional[float] = None
    dpto_min_pasta: Optional[float] = None
    Ppto_react_aridos: Optional[float] = None
    Ppto_react_pasta: Optional[float] = None
    seed: Optional[int] = None

    def to_dict(self):
        return {
            "sieve_size": self.sieve_size,
            "tpp": self.tpp,
            "x": self.x,
            "y": self.y,
            "Pagg": self.Pagg,
            "Pporos": self.Pporos,
            "dporo_min": self.dporo_min,
            "dporo_max": self.dporo_max,
            "r_react": self.r_react,
            "dpto_max_aridos": self.dpto_max_aridos,
            "dpto_min_aridos": self.dpto_min_aridos,
            "dpto_max_pasta": self.dpto_max_pasta,
            "dpto_min_pasta": self.dpto_min_pasta,
            "Ppto_react_aridos": self.Ppto_react_aridos,
            "Ppto_react_pasta": self.Ppto_react_pasta,
            "seed": self.seed,
        }
