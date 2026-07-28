import pytest

from ccrvoc.environment import SequentialEnvironment
from ccrvoc.transitions import do_transition, observational_transition
from ccrvoc.types import Action, ActionType


def test_rollout_uses_do_action_transition(config: dict) -> None:
    env = SequentialEnvironment(config, 12)
    outcome = do_transition(env, Action(ActionType.CONTEXT))
    assert outcome.usable
    with pytest.raises(RuntimeError, match="not causal"):
        observational_transition(env, Action(ActionType.CONTEXT))
