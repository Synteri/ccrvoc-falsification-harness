import numpy as np

from ccrvoc.environment import SequentialEnvironment
from ccrvoc.types import Action, ActionType, EvidenceRecord


def test_repair_can_remove_and_introduce_defects(config: dict) -> None:
    regime = {"regression_min": 1.0, "regression_max": 1.0}
    env = SequentialEnvironment(config, 8, regime_name="repair", regime=regime)
    env.step(Action(ActionType.PRIMARY_GENERATION, agent="A0"))
    latent = env._candidates[0]  # verifier-only inspection
    latent.defects[:] = False
    latent.defects[1] = True
    flags = np.zeros(5, dtype=bool)
    flags[1] = True
    env._evidence.append(EvidenceRecord(0, 0, 0, "unit_test", "test", flags))
    env.agent_world.competence["A2"][1] = 100
    env.step(Action(ActionType.REPAIR, 0, agent="A2", target_mode=1))
    assert not latent.defects[1]
    assert latent.defects[[0, 2, 3, 4]].all()
