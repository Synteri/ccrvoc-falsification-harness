from ccrvoc.environment import SequentialEnvironment
from ccrvoc.policies.ccr_voc import CCRVOCPolicy
from ccrvoc.runtime import execute_policy


def test_policy_terminates_without_post_terminal_actions(config: dict) -> None:
    result = execute_policy(CCRVOCPolicy(config), SequentialEnvironment(config, 15), 0)
    assert result.terminal_action_count == 0
    assert result.cost <= 6.0
