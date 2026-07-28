from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ccrvoc.policies.base import BasePolicy, _flagged_mode
from ccrvoc.types import Action, ActionType, EpisodeResult, PolicyView

ARMS = {
    "generation_unit": ("generate", "unit_test", "independent_review"),
    "generation_review": ("generate", "independent_review"),
    "context_tests": ("context", "generate", "unit_test", "integration_test", "independent_review"),
    "alternatives_review": ("generate", "alternative", "independent_review"),
    "test_heavy": (
        "generate",
        "unit_test",
        "integration_test",
        "fuzz_security",
        "independent_review",
    ),
    "reviewer_heavy": ("generate", "independent_review", "adversarial_review"),
    "two_repair": (
        "generate",
        "independent_review",
        "repair",
        "independent_review",
        "repair",
        "independent_review",
    ),
    "adversarial": ("context", "generate", "adversarial_review", "unit_test"),
}


@dataclass
class ArmStats:
    pulls: np.ndarray
    rewards: np.ndarray
    reward_sq: np.ndarray

    @classmethod
    def empty(cls) -> ArmStats:
        n = len(ARMS)
        return cls(np.zeros(n), np.zeros(n), np.zeros(n))


class MacroPolicy(BasePolicy):
    name = "macro"

    def __init__(self, config: dict, risk_threshold: float = 0.05) -> None:
        super().__init__(config, risk_threshold)
        self.stats = ArmStats.empty()
        self._chosen_arm = 0
        self._last_arm = 0

    def select_arm(self, view: PolicyView) -> int:
        return 0

    def _features(self, view: PolicyView) -> np.ndarray:
        return np.array(
            [
                1.0,
                view.task.value / 5,
                view.task.budget / 6,
                view.task.deadline / 720,
                float(view.context_level),
            ]
        )

    def choose_action(self, view: PolicyView) -> Action:
        safe = self.safe_candidate(view)
        if safe is not None:
            return Action(ActionType.ACCEPT, safe)
        total_actions = sum(view.action_counts.values())
        if total_actions == 0:
            self._chosen_arm = self.select_arm(view)
            self._last_arm = self._chosen_arm
        schedule = list(ARMS.values())[self._chosen_arm]
        if total_actions >= len(schedule):
            return Action(ActionType.DECLARE_FAILURE)
        token = schedule[total_actions]
        cid = view.candidates[-1].candidate_id if view.candidates else None
        if token == "generate":
            return Action(ActionType.PRIMARY_GENERATION, agent="A0")
        if token == "alternative":
            return Action(ActionType.DIVERSE_ALTERNATIVE, agent="A2")
        if token == "context":
            return Action(ActionType.CONTEXT)
        if token == "repair":
            mode = _flagged_mode(view, cid)
            if mode is None:
                return Action(ActionType.INDEPENDENT_REVIEW, cid, "independent_review")
            return Action(ActionType.REPAIR, cid, agent="A2", target_mode=mode)
        return Action(ActionType(token), cid, token)

    def observe_audited(self, result: EpisodeResult, rho: float) -> None:
        if self.frozen:
            raise RuntimeError("audited test reward cannot update frozen bandit")
        reward = result.work - rho * result.cost
        arm = self._last_arm
        self.stats.pulls[arm] += 1
        self.stats.rewards[arm] += reward
        self.stats.reward_sq[arm] += reward**2
