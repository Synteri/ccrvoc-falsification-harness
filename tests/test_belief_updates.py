import numpy as np

from ccrvoc.belief import ParticleBelief
from ccrvoc.types import EvidenceRecord


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
