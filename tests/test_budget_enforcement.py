from ccrvoc.environment import SequentialEnvironment
from ccrvoc.types import Action, ActionType


def test_budget_is_never_exceeded(config: dict) -> None:
    env = SequentialEnvironment(config, 4, regime_name="tiny", regime={"budget_multiplier": 0.001})
    outcome = env.step(Action(ActionType.PRIMARY_GENERATION, agent="A0"))
    assert outcome.reason == "budget_rejected"
    assert env.spent == 0
    assert not env.budget_violation
