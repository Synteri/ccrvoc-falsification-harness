from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ccrvoc.rng import generator
from ccrvoc.types import TaskPublic

CLASS_PROBS = np.array([0.30, 0.20, 0.20, 0.15, 0.15])
CLASSES = np.array(["routine", "ambiguous", "integration", "security", "long_tail"])
CLASS_MEANS = np.array(
    [
        [-0.8, -0.5, -0.8, -1.2, -1.0],
        [0.8, -0.2, 0.0, -0.8, -0.5],
        [0.0, 0.2, 1.0, -0.3, 0.1],
        [0.1, 0.2, 0.4, 1.2, 0.0],
        [0.6, 0.7, 0.7, 0.6, 0.6],
    ]
)
SIGMAS = np.array([0.25, 0.80, 0.55, 0.75, 0.70])
MEDIAN_VALUES = np.array([1.0, 1.5, 2.0, 3.0, 2.5])
BUDGETS = np.array([1.5, 3.0, 4.0, 6.0, 5.0])
DEADLINES = np.array([180.0, 360.0, 480.0, 720.0, 600.0])


@dataclass(frozen=True)
class LatentTask:
    task_id: int
    class_index: int
    task_class: str
    difficulty: NDArray[np.float64]
    trap: NDArray[np.float64]
    value: float
    budget: float
    deadline: float
    catastrophic: bool = False

    def public(self, expose_class: bool = False) -> TaskPublic:
        return TaskPublic(
            self.task_id,
            self.value,
            self.budget,
            self.deadline,
            self.task_class if expose_class else None,
        )


def generate_task(
    root_seed: int,
    task_id: int,
    regime: dict[str, float | bool],
    world: int = 0,
) -> LatentTask:
    rng = generator(root_seed, "task_generation", world, task_id)
    c = int(rng.choice(5, p=CLASS_PROBS))
    shift = float(regime.get("difficulty_shift", 0.0))
    difficulty = CLASS_MEANS[c] + rng.normal(0, 0.5, 5) + shift
    trap = rng.normal(0, SIGMAS[c], 5)
    trap[0] += float(regime.get("spec_trap_shift", 0.0))
    value = float(np.clip(np.exp(np.log(MEDIAN_VALUES[c]) + rng.normal(0, 0.4)), 0.5, 5.0))
    budget = float(BUDGETS[c] * float(regime.get("budget_multiplier", 1.0)))
    deadline = float(DEADLINES[c] * float(regime.get("deadline_multiplier", 1.0)))
    catastrophic = bool(rng.random() < float(regime.get("catastrophic_probability", 0.0)))
    return LatentTask(
        task_id, c, str(CLASSES[c]), difficulty, trap, value, budget, deadline, catastrophic
    )
