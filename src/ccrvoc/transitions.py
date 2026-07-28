from __future__ import annotations

from ccrvoc.environment import SequentialEnvironment
from ccrvoc.types import Action, ActionOutcome


def do_transition(environment: SequentialEnvironment, action: Action) -> ActionOutcome:
    """Explicit interventional transition used by rollouts."""
    return environment.step(action)


def observational_transition(*args: object, **kwargs: object) -> None:
    raise RuntimeError("observational action-success associations are not causal transitions")
