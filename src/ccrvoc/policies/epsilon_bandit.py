from __future__ import annotations

from ccrvoc.policies.macro import ARMS, MacroPolicy
from ccrvoc.rng import generator
from ccrvoc.types import PolicyView


class EpsilonBanditPolicy(MacroPolicy):
    name = "epsilon_bandit"

    def __init__(self, config: dict, risk_threshold: float = 0.05, epsilon: float = 0.10) -> None:
        super().__init__(config, risk_threshold)
        self.epsilon = epsilon
        self.decisions = 0

    def select_arm(self, view: PolicyView) -> int:
        rng = generator(
            self.config["seed"],
            "policy_posterior_sampling",
            self.name,
            self.decisions,
            view.task.task_id,
        )
        self.decisions += 1
        if rng.random() < self.epsilon or (self.stats.pulls == 0).any():
            return int(rng.integers(len(ARMS)))
        return int((self.stats.rewards / self.stats.pulls).argmax())
