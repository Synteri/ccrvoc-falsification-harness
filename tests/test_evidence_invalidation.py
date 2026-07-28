from ccrvoc.environment import SequentialEnvironment
from ccrvoc.policies.generate_review import GenerateReviewPolicy
from ccrvoc.types import Action, ActionType


def _mutated_env(config: dict) -> SequentialEnvironment:
    env = SequentialEnvironment(config, 32)
    env.step(Action(ActionType.PRIMARY_GENERATION, agent="A0"))
    env.step(Action(ActionType.INDEPENDENT_REVIEW, 0, "independent_review"))
    env.step(Action(ActionType.REPAIR, 0, agent="A2", target_mode=0))
    return env


def test_mutation_invalidates_evidence(config: dict) -> None:
    env = _mutated_env(config)
    assert env.stale_invalidations == 1
    assert env.view().evidence[0].stale


def test_stale_evidence_cannot_authorize_acceptance(config: dict) -> None:
    env = _mutated_env(config)
    policy = GenerateReviewPolicy(config, risk_threshold=1.0)
    assert policy.safe_candidate(env.view()) is None
