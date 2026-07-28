from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ccrvoc.evidence import FALSE_POSITIVE, SENSITIVITY
from ccrvoc.rng import generator
from ccrvoc.types import EvidenceRecord, PolicyView


def systematic_resample(weights: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    positions = (rng.random() + np.arange(len(weights))) / len(weights)
    cumulative = np.cumsum(weights)
    return np.searchsorted(cumulative, positions, side="right")


@dataclass
class ParticleBelief:
    defects: np.ndarray
    task_class: np.ndarray
    difficulties: np.ndarray
    competence: np.ndarray
    verifier_sensitivity: np.ndarray
    verifier_fpr: np.ndarray
    source_latents: np.ndarray
    diminishing_beta: np.ndarray
    weights: np.ndarray
    ensemble_member: np.ndarray
    correlation_discount: float = 0.5
    rejuvenations: int = 0

    @classmethod
    def initialize(
        cls, config: dict, task_id: int, candidate_prior: float = 0.30
    ) -> ParticleBelief:
        n = int(config["particles"])
        m = int(config["ensemble_members"])
        rng = generator(config["seed"], "policy_posterior_sampling", task_id, "belief")
        task_class = rng.choice(5, size=n, p=[0.3, 0.2, 0.2, 0.15, 0.15])
        difficulties = rng.normal(0, 1, size=(n, 5))
        defects = rng.random((n, 5)) < candidate_prior
        competence = rng.normal(0.7, 0.4, size=(n, 3, 5))
        verifier_sensitivity = np.clip(rng.normal(1.0, 0.10, size=(n, 6, 5)), 0.1, 1.5)
        verifier_fpr = np.clip(rng.normal(1.0, 0.15, size=(n, 6)), 0.2, 3.0)
        source_latents = rng.normal(size=(n, 6, 5))
        diminishing_beta = np.clip(rng.normal(0.4, 0.15, size=(n, 7)), 0.01, 1.2)
        ensemble_member = np.arange(n) % m
        return cls(
            defects,
            task_class,
            difficulties,
            competence,
            verifier_sensitivity,
            verifier_fpr,
            source_latents,
            diminishing_beta,
            np.full(n, 1 / n),
            ensemble_member,
        )

    def reset_candidate_prior(self, probability: np.ndarray | float) -> None:
        rng = np.random.default_rng(1729 + self.rejuvenations)
        p = np.asarray(probability)
        if p.ndim == 0:
            p = np.full((len(self.weights), 5), float(p))
        elif p.shape == (5,):
            p = np.broadcast_to(p, (len(self.weights), 5))
        self.defects = rng.random((len(self.weights), 5)) < p
        self.weights.fill(1 / len(self.weights))

    def update_evidence(self, evidence: EvidenceRecord, repeated_count: int = 0) -> None:
        names = list(SENSITIVITY)
        source = evidence.source if evidence.source in SENSITIVITY else "independent_review"
        source_idx = names.index(source)
        sens = np.clip(
            SENSITIVITY[source][None, :] * self.verifier_sensitivity[:, source_idx, :],
            1e-4,
            1 - 1e-4,
        )
        fpr = np.clip(
            FALSE_POSITIVE[source] * self.verifier_fpr[:, source_idx, None],
            1e-4,
            1 - 1e-4,
        )
        p_flag = np.where(self.defects, sens, fpr)
        likelihood = np.where(evidence.flags[None, :], p_flag, 1 - p_flag).prod(axis=1)
        if repeated_count:
            likelihood = np.power(likelihood, self.correlation_discount)
        likelihood = np.maximum(likelihood, 1e-12)
        self.weights *= likelihood
        total = self.weights.sum()
        if not np.isfinite(total) or total <= 0:
            self.weights.fill(1 / len(self.weights))
            self.rejuvenations += 1
            return
        self.weights /= total
        ess = 1 / np.square(self.weights).sum()
        if ess < len(self.weights) / 2:
            rng = np.random.default_rng(991 + self.rejuvenations)
            idx = systematic_resample(self.weights, rng)
            for name in (
                "defects",
                "task_class",
                "difficulties",
                "competence",
                "verifier_sensitivity",
                "verifier_fpr",
                "source_latents",
                "diminishing_beta",
                "ensemble_member",
            ):
                setattr(self, name, getattr(self, name)[idx].copy())
            flip = rng.random(self.defects.shape) < 0.002
            self.defects ^= flip
            self.weights.fill(1 / len(self.weights))
            self.rejuvenations += 1

    def mode_probabilities(self) -> np.ndarray:
        return np.average(self.defects, axis=0, weights=self.weights)

    def risk_by_ensemble(self) -> np.ndarray:
        risks = []
        for member in np.unique(self.ensemble_member):
            mask = self.ensemble_member == member
            w = self.weights[mask]
            if w.sum() <= 0:
                risks.append(1.0)
                continue
            incorrect = self.defects[mask].any(axis=1)
            risks.append(float(np.average(incorrect, weights=w)))
        return np.array(risks)

    def robust_risk(self, quantile: float = 0.95) -> float:
        return float(np.quantile(self.risk_by_ensemble(), quantile))


def evidence_is_acceptance_eligible(view: PolicyView, candidate_id: int) -> bool:
    candidates = {c.candidate_id: c for c in view.candidates}
    if candidate_id not in candidates:
        return False
    candidate = candidates[candidate_id]
    current = [
        e
        for e in view.evidence
        if not e.stale
        and e.candidate_id == candidate_id
        and e.candidate_version == candidate.version
    ]
    return bool(current) and any(e.independent_of_agent for e in current)
