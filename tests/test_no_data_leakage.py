import pytest

from ccrvoc.calibration import FrozenCalibration, assert_no_test_leakage
from ccrvoc.causal_model import LearnedCausalModel, OverlapDiagnostics
from ccrvoc.policies.generate_review import GenerateReviewPolicy


def test_test_ids_cannot_enter_calibration() -> None:
    frozen = FrozenCalibration("p", 0.01, (100, 101), 0.99, True)
    with pytest.raises(AssertionError, match="test labels"):
        assert_no_test_leakage(frozen, set(), set(), {101})


def test_frozen_policy_and_model_reject_mutation(config: dict) -> None:
    policy = GenerateReviewPolicy(config)
    policy.freeze()
    with pytest.raises(RuntimeError):
        policy.set_threshold(0.1)
    model = LearnedCausalModel({}, OverlapDiagnostics({}, 0.05, 0))
    model.freeze()
    with pytest.raises(RuntimeError):
        model.fit(None)  # type: ignore[arg-type]
