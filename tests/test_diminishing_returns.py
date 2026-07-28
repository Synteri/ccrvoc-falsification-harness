from ccrvoc.environment import SequentialEnvironment
from ccrvoc.types import Action, ActionType


def test_repeated_context_has_diminishing_increment(config: dict) -> None:
    env = SequentialEnvironment(config, 1)
    env.step(Action(ActionType.CONTEXT))
    first = env.context_level
    env.step(Action(ActionType.CONTEXT))
    second_increment = env.context_level - first
    assert 0 < second_increment < first
