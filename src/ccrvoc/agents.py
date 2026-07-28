from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ccrvoc.rng import generator

NOMINAL = {
    "A0": np.array([0.7, 1.0, 0.7, 0.4, 0.6]),
    "A1": np.array([0.6, 0.9, 0.8, 0.5, 0.6]),
    "A2": np.array([0.8, 0.7, 0.8, 0.9, 0.7]),
}
FAMILY = {"A0": "F01", "A1": "F01", "A2": "F2"}
FAMILIES = tuple(dict.fromkeys(FAMILY.values()))


@dataclass(frozen=True)
class AgentWorld:
    competence: dict[str, NDArray[np.float64]]
    family_shocks: dict[str, NDArray[np.float64]]


def sample_agent_world(root_seed: int, world: int = 0, period: int = 0) -> AgentWorld:
    rng = generator(root_seed, "actual_agent_outcomes", "world", world, period)
    competence = {name: nominal + rng.normal(0, 0.3, 5) for name, nominal in NOMINAL.items()}
    family_shocks = {family: rng.normal(0, 0.4, 5) for family in FAMILIES}
    return AgentWorld(competence, family_shocks)
