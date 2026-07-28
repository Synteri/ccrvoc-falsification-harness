import numpy as np

from ccrvoc.belief import ParticleBelief
from ccrvoc.policies.ccr_voc import CCRVOCPolicy
from ccrvoc.types import CandidatePublic, EvidenceRecord, PolicyView, TaskPublic


def _negative(eid: int, source: str) -> EvidenceRecord:
    return EvidenceRecord(
        eid, 0, 0, source, "test", np.zeros(5, dtype=bool), independent_of_agent=True
    )


def test_negative_evidence_reduces_risk(config: dict) -> None:
    belief = ParticleBelief.initialize(config, 1)
    before = belief.robust_risk()
    belief.update_evidence(_negative(0, "independent_review"))
    assert belief.robust_risk() < before


def test_correlated_repeat_moves_less_than_independent(config: dict) -> None:
    independent = ParticleBelief.initialize(config, 2)
    correlated = ParticleBelief.initialize(config, 2)
    first = _negative(0, "independent_review")
    second = _negative(1, "independent_review")
    independent.update_evidence(first)
    correlated.update_evidence(first)
    before = independent.robust_risk()
    independent.update_evidence(second, repeated_count=0)
    correlated.update_evidence(second, repeated_count=1)
    assert independent.robust_risk() < correlated.robust_risk() < before


def test_stale_evidence_is_removed_from_particle_belief_after_mutation(
    config: dict,
) -> None:
    flags = np.zeros(5, dtype=bool)
    flags[0] = True
    evidence = EvidenceRecord(
        0,
        0,
        0,
        "spec_review",
        "reviewer",
        flags,
        independent_of_agent=True,
    )
    task = TaskPublic(1, 2.0, 6.0, 720.0)
    version_zero = CandidatePublic(0, 0, "A0", "F01", 0.5)
    flagged_view = PolicyView(task, (version_zero,), (evidence,), 0.5, 0.0, 0.0, {}, False)
    clean_view = PolicyView(task, (version_zero,), (), 0.5, 0.0, 0.0, {}, False)
    version_one = CandidatePublic(
        0,
        1,
        "A0",
        "F01",
        0.5,
        prior_repairs=[1, 0, 0, 0, 0],
    )
    evidence.stale = True
    mutated_view = PolicyView(task, (version_one,), (evidence,), 0.5, 0.0, 0.0, {}, False)
    previously_flagged = CCRVOCPolicy(config)
    unobserved = CCRVOCPolicy(config)
    previously_flagged.risk_score(flagged_view, 0)
    unobserved.risk_score(clean_view, 0)
    risk_after_flag = previously_flagged.risk_score(mutated_view, 0)
    risk_without_flag = unobserved.risk_score(mutated_view, 0)
    assert risk_after_flag == risk_without_flag
