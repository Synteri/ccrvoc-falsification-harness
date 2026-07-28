from __future__ import annotations

import numpy as np

from ccrvoc.policies.macro import MacroPolicy
from ccrvoc.rng import generator
from ccrvoc.types import PolicyView


class ThompsonPolicy(MacroPolicy):
    name = "thompson"

    def select_arm(self, view: PolicyView) -> int:
        rng = generator(
            self.config["seed"], "policy_posterior_sampling", self.name, view.task.task_id
        )
        n = np.maximum(self.stats.pulls, 1)
        mean = self.stats.rewards / n
        variance = np.maximum(self.stats.reward_sq / n - mean**2, 0.1)
        samples = rng.normal(mean, np.sqrt(variance / n))
        samples[self.stats.pulls == 0] += 1e3
        return int(samples.argmax())
