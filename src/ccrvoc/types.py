from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]

MODES = ("specification", "logic", "integration", "security", "performance")
TASK_CLASSES = ("routine", "ambiguous", "integration", "security", "long_tail")


class ActionType(StrEnum):
    PRIMARY_GENERATION = "primary_generation"
    CONTEXT = "context"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    FUZZ_SECURITY = "fuzz_security"
    SAME_FAMILY_ALTERNATIVE = "same_family_alternative"
    DIVERSE_ALTERNATIVE = "diverse_alternative"
    DEBUG = "debug"
    INDEPENDENT_REVIEW = "independent_review"
    ADVERSARIAL_REVIEW = "adversarial_review"
    REVIEWER_RERUN = "reviewer_rerun"
    REPAIR = "repair"
    ACCEPT = "accept"
    DECLARE_FAILURE = "declare_failure"


class TerminalDecision(StrEnum):
    ACCEPT = "accept"
    FAILURE = "failure"


@dataclass(frozen=True)
class TaskPublic:
    task_id: int
    value: float
    budget: float
    deadline: float
    task_class: str | None = None


@dataclass(frozen=True)
class Action:
    kind: ActionType
    candidate_id: int | None = None
    source: str | None = None
    agent: str | None = None
    target_mode: int | None = None
    prompt_variant: int = 0


@dataclass
class CandidatePublic:
    candidate_id: int
    version: int
    agent: str
    family: str
    context_level: float
    prior_repairs: list[int] = field(default_factory=lambda: [0] * 5)


@dataclass
class EvidenceRecord:
    evidence_id: int
    candidate_id: int
    candidate_version: int
    source: str
    family: str
    flags: BoolArray
    stale: bool = False
    independent_of_agent: bool = True
    full_system: bool = False
    completed_at: float = 0.0


@dataclass(frozen=True)
class ActionOutcome:
    usable: bool
    cost: float
    duration: float
    reason: str
    candidate_id: int | None = None
    candidate_version: int | None = None
    evidence_id: int | None = None
    hints: tuple[bool, ...] | None = None
    changed_modes: tuple[int, ...] = ()


@dataclass(frozen=True)
class PolicyView:
    task: TaskPublic
    candidates: tuple[CandidatePublic, ...]
    evidence: tuple[EvidenceRecord, ...]
    context_level: float
    spent: float
    elapsed: float
    action_counts: Mapping[str, int]
    terminal: bool

    @staticmethod
    def readonly_counts(counts: Mapping[str, int]) -> Mapping[str, int]:
        return MappingProxyType(dict(counts))


@dataclass
class EpisodeResult:
    task_id: int
    policy: str
    regime: str
    seed: int
    accepted: bool
    correct: bool
    value: float
    cost: float
    elapsed: float
    deadline_miss: bool
    budget_violation: bool
    scheduler_seconds: float
    stale_invalidations: int
    task_class: str
    action_counts: dict[str, int]
    severity_false_accept: float = 0.0
    terminal_action_count: int = 0

    @property
    def work(self) -> float:
        return self.value if self.accepted and self.correct else 0.0

    def as_dict(self) -> dict[str, Any]:
        row = self.__dict__.copy()
        row["work"] = self.work
        row["far_numerator"] = int(self.accepted and not self.correct)
        return row
