from ccrvoc.environment import SequentialEnvironment
from ccrvoc.types import Action, ActionType


def test_late_action_consumes_resources_but_returns_nothing(config: dict) -> None:
    env = SequentialEnvironment(
        config, 5, regime_name="deadline", regime={"deadline_multiplier": 0.00001}
    )
    outcome = env.step(Action(ActionType.PRIMARY_GENERATION, agent="A0"))
    assert not outcome.usable
    assert outcome.reason == "deadline"
    assert outcome.cost > 0 and outcome.duration > 0
    assert env.spent > 0 and not env.view().candidates


def test_terminal_state_is_absorbing(config: dict) -> None:
    env = SequentialEnvironment(config, 6)
    env.step(Action(ActionType.DECLARE_FAILURE))
    outcome = env.step(Action(ActionType.CONTEXT))
    assert outcome.reason == "terminal_absorbing"
    assert env.spent == 0
