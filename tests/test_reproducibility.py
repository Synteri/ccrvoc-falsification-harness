import json
import os
import subprocess
import sys

from ccrvoc.environment import SequentialEnvironment
from ccrvoc.policies.generate_review import GenerateReviewPolicy
from ccrvoc.runtime import execute_policy


def test_deterministic_episode(config: dict) -> None:
    a = execute_policy(GenerateReviewPolicy(config), SequentialEnvironment(config, 71), 0).as_dict()
    b = execute_policy(GenerateReviewPolicy(config), SequentialEnvironment(config, 71), 0).as_dict()
    a.pop("scheduler_seconds")
    b.pop("scheduler_seconds")
    assert a == b


def test_agent_world_is_stable_across_python_hash_seeds() -> None:
    script = """
import json
from ccrvoc.agents import sample_agent_world
world = sample_agent_world(20260728)
print(json.dumps({
    "competence": {key: value.tolist() for key, value in world.competence.items()},
    "family_shocks": {key: value.tolist() for key, value in world.family_shocks.items()},
}, sort_keys=True))
"""
    outputs = []
    for hash_seed in ("0", "1"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = hash_seed
        outputs.append(
            subprocess.check_output([sys.executable, "-c", script], text=True, env=env).strip()
        )

    assert json.loads(outputs[0]) == json.loads(outputs[1])
