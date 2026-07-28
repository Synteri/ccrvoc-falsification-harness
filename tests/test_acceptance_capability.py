import numpy as np

from ccrvoc.actions import candidate_actions
from ccrvoc.environment import SequentialEnvironment
from ccrvoc.policies.ccr_voc import CCRVOCPolicy
from ccrvoc.policies.fixed_compute import FixedComputePolicy
from ccrvoc.types import (
    ActionType,
    CandidatePublic,
    EvidenceRecord,
    PolicyView,
    TaskPublic,
)

SOURCES = (
    "unit_test",
    "integration_test",
    "fuzz_security",
    "independent_review",
    "adversarial_review",
    "spec_review",
)


def clean_view(
    flagged_source: str | None = None,
    flagged_mode: int | None = None,
) -> PolicyView:
    candidate = CandidatePublic(0, 0, "A0", "F01", 0.5)
    evidence = []
    for evidence_id, source in enumerate(SOURCES):
        flags = np.zeros(5, dtype=bool)
        if source == flagged_source and flagged_mode is not None:
            flags[flagged_mode] = True
        evidence.append(
            EvidenceRecord(
                evidence_id,
                0,
                0,
                source,
                "reviewer" if "review" in source else "test",
                flags,
                independent_of_agent=True,
            )
        )
    return PolicyView(
        TaskPublic(1, 2.0, 6.0, 720.0),
        (candidate,),
        tuple(evidence),
        0.5,
        0.0,
        0.0,
        {},
        False,
    )


def test_scheduled_policy_advances_through_declared_tokens(config: dict) -> None:
    policy = FixedComputePolicy(config, risk_threshold=0.0)
    env = SequentialEnvironment(
        config,
        44,
        regime_name="schedule_fixture",
        regime={"budget_multiplier": 10.0},
    )
    trace = []
    for _ in range(len(policy.schedule)):
        action = policy.choose_action(env.view())
        trace.append((action.kind.value, action.source))
        env.step(action)
    assert trace == [
        ("context", None),
        ("primary_generation", None),
        ("unit_test", "unit_test"),
        ("integration_test", "integration_test"),
        ("fuzz_security", "fuzz_security"),
        ("independent_review", "independent_review"),
        ("independent_review", "spec_review"),
        ("adversarial_review", "adversarial_review"),
    ]


def test_clean_full_coverage_fixture_is_acceptable(config: dict) -> None:
    view = clean_view()
    heuristic = FixedComputePolicy(config, risk_threshold=0.20)
    particle = CCRVOCPolicy(config, risk_threshold=0.20)
    assert heuristic.risk_score(view, 0) < 0.20
    assert particle.risk_score(view, 0) < 0.20
    assert heuristic.safe_candidate(view) == 0
    assert particle.safe_candidate(view) == 0


def test_mode_specific_flags_block_acceptance(config: dict) -> None:
    source_by_mode = {
        0: "spec_review",
        1: "unit_test",
        2: "integration_test",
        3: "fuzz_security",
        4: "adversarial_review",
    }
    policy = FixedComputePolicy(config, risk_threshold=0.20)
    for mode, source in source_by_mode.items():
        view = clean_view(source, mode)
        assert policy.risk_score(view, 0) > 0.20
        assert policy.safe_candidate(view) is None


def test_action_set_exposes_specification_review(config: dict) -> None:
    view = clean_view()
    sources = {action.source for action in candidate_actions(view)}
    assert "spec_review" in sources


def test_unverified_candidate_must_be_checked_before_diversification() -> None:
    candidate = CandidatePublic(0, 0, "A0", "F01", 0.0)
    view = PolicyView(
        TaskPublic(1, 2.0, 6.0, 720.0),
        (candidate,),
        (),
        0.0,
        0.0,
        0.0,
        {},
        False,
    )
    kinds = {action.kind for action in candidate_actions(view)}
    assert ActionType.SAME_FAMILY_ALTERNATIVE not in kinds
    assert ActionType.DIVERSE_ALTERNATIVE not in kinds
