from __future__ import annotations

import time

from ccrvoc.environment import SequentialEnvironment
from ccrvoc.policies.base import BasePolicy
from ccrvoc.types import Action, ActionType, EpisodeResult


def execute_policy(
    policy: BasePolicy, environment: SequentialEnvironment, seed: int
) -> EpisodeResult:
    """Trusted driver: policy receives only PolicyView, never the environment/oracle."""
    scheduler = 0.0
    for _ in range(64):
        view = environment.view()
        if view.terminal:
            break
        start = time.perf_counter()
        action = policy.choose_action(view)
        scheduler += time.perf_counter() - start
        outcome = environment.step(action)
        if outcome.reason == "budget_rejected":
            environment.step(Action(ActionType.DECLARE_FAILURE))
        if environment.elapsed > environment.task.deadline and environment.terminal is None:
            environment.step(Action(ActionType.DECLARE_FAILURE))
    if environment.terminal is None:
        environment.step(Action(ActionType.DECLARE_FAILURE))
    return environment.finalize(policy.name, seed, scheduler)
