from ccrvoc.environment import SequentialEnvironment
from ccrvoc.policies.generate_review import GenerateReviewPolicy
from ccrvoc.runtime import execute_policy


def test_deterministic_episode(config: dict) -> None:
    a = execute_policy(GenerateReviewPolicy(config), SequentialEnvironment(config, 71), 0).as_dict()
    b = execute_policy(GenerateReviewPolicy(config), SequentialEnvironment(config, 71), 0).as_dict()
    a.pop("scheduler_seconds")
    b.pop("scheduler_seconds")
    assert a == b
