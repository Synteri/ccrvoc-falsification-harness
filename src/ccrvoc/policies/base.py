from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ccrvoc.belief import evidence_is_acceptance_eligible
from ccrvoc.evidence import FALSE_POSITIVE, SENSITIVITY
from ccrvoc.types import Action, ActionType, PolicyView


class BasePolicy(ABC):
    name = "base"

    def __init__(self, config: dict, risk_threshold: float = 0.05) -> None:
        self.config = config
        self.risk_threshold = risk_threshold
        self.frozen = False

    def clone(self) -> BasePolicy:
        return type(self)(self.config, self.risk_threshold)

    def freeze(self) -> None:
        self.frozen = True

    def set_threshold(self, threshold: float) -> None:
        if self.frozen:
            raise RuntimeError("final testing cannot mutate policy hyperparameters")
        self.risk_threshold = float(threshold)

    def risk_score(self, view: PolicyView, candidate_id: int) -> float:
        p = self.mode_probabilities(view, candidate_id)
        return float(1 - np.prod(1 - p))

    def mode_probabilities(self, view: PolicyView, candidate_id: int) -> np.ndarray:
        candidate = next(c for c in view.candidates if c.candidate_id == candidate_id)
        p = np.full(5, np.clip(0.30 * np.exp(-0.8 * candidate.context_level), 0.02, 0.8))
        seen: dict[str, int] = {}
        evidence = [
            e
            for e in view.evidence
            if not e.stale
            and e.candidate_id == candidate_id
            and e.candidate_version == candidate.version
        ]
        for record in evidence:
            source = record.source if record.source in SENSITIVITY else "independent_review"
            sens = SENSITIVITY[source]
            fpr = FALSE_POSITIVE[source]
            likelihood_defect = np.where(record.flags, sens, 1 - sens)
            likelihood_clean = np.where(record.flags, fpr, 1 - fpr)
            count = seen.get(source, 0)
            discount = 1.0 if count == 0 else 0.35
            odds = p / np.maximum(1 - p, 1e-12)
            odds *= np.power(likelihood_defect / likelihood_clean, discount)
            p = odds / (1 + odds)
            seen[source] = count + 1
        return p

    def safe_candidate(self, view: PolicyView) -> int | None:
        eligible: list[tuple[float, int]] = []
        for candidate in view.candidates:
            if not evidence_is_acceptance_eligible(view, candidate.candidate_id):
                continue
            risk = self.risk_score(view, candidate.candidate_id)
            if risk <= self.risk_threshold:
                eligible.append((risk, candidate.candidate_id))
        return min(eligible)[1] if eligible else None

    @abstractmethod
    def choose_action(self, view: PolicyView) -> Action:
        raise NotImplementedError


class ScheduledPolicy(BasePolicy):
    schedule: tuple[str, ...] = ()

    def __init__(self, config: dict, risk_threshold: float = 0.05) -> None:
        super().__init__(config, risk_threshold)
        self._schedule_index = 0

    def choose_action(self, view: PolicyView) -> Action:
        safe = self.safe_candidate(view)
        if safe is not None:
            return Action(ActionType.ACCEPT, safe)
        if self._schedule_index >= len(self.schedule):
            return Action(ActionType.DECLARE_FAILURE)
        token = self.schedule[self._schedule_index]
        self._schedule_index += 1
        latest = view.candidates[-1].candidate_id if view.candidates else None
        if token == "context":
            return Action(ActionType.CONTEXT)
        if token == "generate":
            return Action(ActionType.PRIMARY_GENERATION, agent="A0")
        if token == "alternative":
            return Action(ActionType.DIVERSE_ALTERNATIVE, agent="A2")
        if token in {"unit_test", "integration_test", "fuzz_security"}:
            return Action(ActionType(token), latest, token)
        if token in {"independent_review", "adversarial_review"}:
            return Action(ActionType(token), latest, token)
        if token == "spec_review":
            return Action(ActionType.INDEPENDENT_REVIEW, latest, "spec_review")
        if token == "repair":
            mode = _flagged_mode(view, latest)
            if mode is None:
                return Action(ActionType.INDEPENDENT_REVIEW, latest, "independent_review")
            return Action(ActionType.REPAIR, latest, agent="A2", target_mode=mode)
        raise ValueError(token)


def _flagged_mode(view: PolicyView, candidate_id: int | None) -> int | None:
    for evidence in reversed(view.evidence):
        if evidence.stale or evidence.candidate_id != candidate_id:
            continue
        flagged = np.flatnonzero(evidence.flags)
        if len(flagged):
            return int(flagged[0])
    return None
