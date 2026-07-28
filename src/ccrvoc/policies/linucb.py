from __future__ import annotations

import numpy as np

from ccrvoc.policies.macro import ARMS, MacroPolicy
from ccrvoc.types import EpisodeResult, PolicyView


class LinUCBPolicy(MacroPolicy):
    name = "linucb"

    def __init__(self, config: dict, risk_threshold: float = 0.05, alpha: float = 1.0) -> None:
        super().__init__(config, risk_threshold)
        self.alpha = alpha
        self.a = np.array([np.eye(5) for _ in ARMS])
        self.b = np.zeros((len(ARMS), 5))
        self._last_x = np.ones(5)

    def select_arm(self, view: PolicyView) -> int:
        x = self._features(view)
        self._last_x = x
        scores = []
        for arm in range(len(ARMS)):
            inv = np.linalg.inv(self.a[arm])
            theta = inv @ self.b[arm]
            scores.append(theta @ x + self.alpha * np.sqrt(x @ inv @ x))
        return int(np.argmax(scores))

    def observe_audited(self, result: EpisodeResult, rho: float) -> None:
        super().observe_audited(result, rho)
        reward = result.work - rho * result.cost
        arm = self._last_arm
        self.a[arm] += np.outer(self._last_x, self._last_x)
        self.b[arm] += reward * self._last_x


class LinearThompsonPolicy(LinUCBPolicy):
    name = "linear_thompson"

    def select_arm(self, view: PolicyView) -> int:
        x = self._features(view)
        self._last_x = x
        rng = np.random.default_rng(self.config["seed"] + view.task.task_id)
        scores = []
        for arm in range(len(ARMS)):
            inv = np.linalg.inv(self.a[arm])
            mean = inv @ self.b[arm]
            theta = rng.multivariate_normal(mean, inv)
            scores.append(theta @ x)
        return int(np.argmax(scores))
