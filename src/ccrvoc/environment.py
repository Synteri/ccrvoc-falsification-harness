from __future__ import annotations

import math
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
from scipy.special import expit, logit

from ccrvoc.actions import MUTATIONS, VERIFICATION, similarity
from ccrvoc.agents import FAMILY as AGENT_FAMILY
from ccrvoc.agents import AgentWorld, sample_agent_world
from ccrvoc.evidence import FALSE_POSITIVE, SENSITIVITY, copula_flags
from ccrvoc.rng import EpisodeRNG, named_seed
from ccrvoc.tasks import LatentTask, generate_task
from ccrvoc.types import (
    Action,
    ActionOutcome,
    ActionType,
    CandidatePublic,
    EpisodeResult,
    EvidenceRecord,
    PolicyView,
    TerminalDecision,
)

BASE_DEFECT_LOGITS = np.array([-1.0, -0.7, -0.8, -1.3, -1.1])
BASE_REGRESSION = np.array([0.02, 0.02, 0.03, 0.01, 0.02])
SEVERITY = np.array([1.0, 1.0, 1.2, 2.0, 1.1])
BETA = {
    ActionType.PRIMARY_GENERATION: 0.40,
    ActionType.CONTEXT: 0.35,
    ActionType.UNIT_TEST: 0.80,
    ActionType.INTEGRATION_TEST: 0.80,
    ActionType.FUZZ_SECURITY: 0.80,
    ActionType.REVIEWER_RERUN: 0.70,
    ActionType.DEBUG: 0.30,
    ActionType.REPAIR: 0.30,
    ActionType.SAME_FAMILY_ALTERNATIVE: 0.40,
    ActionType.DIVERSE_ALTERNATIVE: 0.10,
    ActionType.INDEPENDENT_REVIEW: 0.15,
    ActionType.ADVERSARIAL_REVIEW: 0.15,
}


@dataclass
class _LatentCandidate:
    public: CandidatePublic
    defects: np.ndarray
    catastrophic: bool = False
    last_modifier_family: str = ""


class SequentialEnvironment:
    """Environment owns oracle state; policy-facing objects contain no defect labels."""

    def __init__(
        self,
        config: dict,
        task_id: int,
        regime_name: str = "balanced_default",
        regime: dict | None = None,
        world: int = 0,
        expose_class: bool = False,
        invalidate_evidence: bool = True,
    ) -> None:
        self.config = config
        self.regime_name = regime_name
        self.regime = dict(regime or {})
        self.task: LatentTask = generate_task(config["seed"], task_id, self.regime, world)
        drift_period = int(self.regime.get("competence_resample_period", 0) or 0)
        period = task_id // drift_period if drift_period else 0
        self.agent_world: AgentWorld = sample_agent_world(config["seed"], world, period)
        self.rng = EpisodeRNG(config["seed"], task_id, world)
        self.expose_class = expose_class
        self.invalidate_evidence = invalidate_evidence
        self.context_level = 0.0
        self.spent = 0.0
        self.elapsed = 0.0
        self.terminal: TerminalDecision | None = None
        self.accepted_candidate: int | None = None
        self._candidates: dict[int, _LatentCandidate] = {}
        self._evidence: list[EvidenceRecord] = []
        self._actions: list[Action] = []
        self.action_counts: Counter[str] = Counter()
        self.same_agent_attempts: Counter[str] = Counter()
        self.stale_invalidations = 0
        self.deadline_miss = False
        self.budget_violation = False
        self.post_terminal_attempts = 0

    def view(self) -> PolicyView:
        candidates = tuple(deepcopy(c.public) for c in self._candidates.values())
        evidence: list[EvidenceRecord] = []
        for record in self._evidence:
            copy = deepcopy(record)
            copy.flags = copy.flags.copy()
            copy.flags.setflags(write=False)
            evidence.append(copy)
        return PolicyView(
            self.task.public(self.expose_class),
            candidates,
            tuple(evidence),
            self.context_level,
            self.spent,
            self.elapsed,
            PolicyView.readonly_counts(self.action_counts),
            self.terminal is not None,
        )

    def _n_eff(self, action: Action) -> float:
        return float(sum(similarity(action, prior) for prior in self._actions))

    def _sample_cost_duration(self, action: Action) -> tuple[float, float]:
        means = self.config["action_means"][action.kind.value]
        cost_rng = self.rng.get("action_costs", len(self._actions), action.kind.value)
        duration_rng = self.rng.get("durations", len(self._actions), action.kind.value)
        if "pareto_shape" in self.regime:
            shape = float(self.regime["pareto_shape"])
            cost = float(means["cost"] * (shape - 1) / shape * (cost_rng.pareto(shape) + 1))
            duration = float(
                means["seconds"] * (shape - 1) / shape * (duration_rng.pareto(shape) + 1)
            )
            return cost, duration
        cost_cv = float(self.config["cost_cv"])
        sigma = math.sqrt(math.log1p(cost_cv**2))
        mu = math.log(float(means["cost"])) - sigma**2 / 2
        cost = float(cost_rng.lognormal(mu, sigma))
        duration_cv = float(self.config["duration_cv"])
        shape = 1 / duration_cv**2
        scale = float(means["seconds"]) / shape
        return cost, float(duration_rng.gamma(shape, scale))

    def feasible(self, action: Action) -> bool:
        if action.kind in {ActionType.ACCEPT, ActionType.DECLARE_FAILURE}:
            return not self.terminal
        if action.kind.value not in self.config["action_means"]:
            return False
        cost, _ = self._sample_cost_duration(action)
        return self.spent + cost <= self.task.budget + 1e-12

    def _generation(self, action: Action, usable: bool) -> ActionOutcome:
        if not usable:
            return ActionOutcome(False, 0, 0, "deadline")
        agent = action.agent or "A0"
        family = AGENT_FAMILY[agent]
        diversity = {
            ActionType.PRIMARY_GENERATION: 0.0,
            ActionType.SAME_FAMILY_ALTERNATIVE: 0.3,
            ActionType.DIVERSE_ALTERNATIVE: 1.0,
        }[action.kind]
        n_eff = self._n_eff(action)
        logits = (
            BASE_DEFECT_LOGITS
            + self.task.difficulty
            + self.task.trap
            + self.agent_world.family_shocks[family]
            - self.agent_world.competence[agent]
            - 0.8 * self.context_level
            - 0.5 * diversity
            + 0.4 * self.same_agent_attempts[agent]
            + BETA[action.kind] * n_eff
        )
        rng = self.rng.get("actual_agent_outcomes", len(self._actions), action.kind.value, agent)
        defects = rng.random(5) < expit(logits)
        cid = len(self._candidates)
        public = CandidatePublic(cid, 0, agent, family, self.context_level)
        self._candidates[cid] = _LatentCandidate(public, defects, self.task.catastrophic, family)
        self.same_agent_attempts[agent] += 1
        return ActionOutcome(True, 0, 0, "generated", cid, 0)

    def _context(self, action: Action, usable: bool) -> ActionOutcome:
        if not usable:
            return ActionOutcome(False, 0, 0, "deadline")
        n_eff = self._n_eff(action)
        gain = 0.7 * math.exp(-BETA[ActionType.CONTEXT] * n_eff)
        new_context = 1 - (1 - self.context_level) * math.exp(-gain)
        self.context_level = new_context
        latest = self._candidates[max(self._candidates)] if self._candidates else None
        actual = latest.defects if latest else np.zeros(5, dtype=bool)
        sensitivity = 0.65 + 0.20 * new_context
        probabilities = np.where(actual, sensitivity, 0.10)
        rng = self.rng.get("actual_evidence_outcomes", len(self._actions), "context")
        hints = tuple(bool(x) for x in (rng.random(5) < probabilities))
        return ActionOutcome(True, 0, 0, "context", hints=hints)

    def _gamma(self, action: Action, source: str) -> float:
        prior_same = [
            a for a in self._actions if a.source == source and a.candidate_id == action.candidate_id
        ]
        if prior_same:
            gamma = float(self.config["family_gamma"]["exact_rerun"])
        elif source in {"independent_review", "adversarial_review", "spec_review"}:
            gamma = float(self.config["family_gamma"]["independent_reviewer_family"])
        else:
            gamma = float(self.config["family_gamma"]["different_model_same_suite"])
        gamma *= float(self.regime.get("gamma_multiplier", 1.0))
        if source in {"independent_review", "adversarial_review"}:
            gamma = float(self.regime.get("true_reviewer_gamma", gamma))
        return float(np.clip(gamma, 0, 0.999))

    def _verification(self, action: Action, usable: bool) -> ActionOutcome:
        if not usable:
            return ActionOutcome(False, 0, 0, "deadline")
        if action.candidate_id not in self._candidates:
            return ActionOutcome(False, 0, 0, "missing_candidate")
        candidate = self._candidates[action.candidate_id]
        source = action.source or action.kind.value
        if source == "reviewer_rerun":
            source = "independent_review"
        sensitivity = SENSITIVITY[source].copy()
        sensitivity *= float(self.regime.get("sensitivity_multiplier", 1.0))
        sensitivity *= float(self.regime.get("post_calibration_sensitivity_multiplier", 1.0))
        fpr = FALSE_POSITIVE[source] * float(self.regime.get("false_positive_multiplier", 1.0))
        probabilities = np.where(candidate.defects, sensitivity, fpr)
        n_eff = self._n_eff(action)
        beta = BETA.get(action.kind, 0.15)
        probabilities = expit(logit(np.clip(probabilities, 1e-6, 1 - 1e-6)) - beta * n_eff)
        gamma = self._gamma(action, source)
        lineage = f"{source}:{action.candidate_id}"
        z_rng = np.random.default_rng(
            named_seed(self.config["seed"], "actual_evidence_outcomes", self.task.task_id, lineage)
        )
        shared_z = z_rng.normal(size=5)
        eps = self.rng.get(
            "actual_evidence_outcomes", len(self._actions), source, action.candidate_id
        ).normal(size=5)
        flags, _ = copula_flags(probabilities, gamma, shared_z, eps)
        if self.regime.get("confidence_inversion", False) and candidate.defects.any():
            flags = ~flags
        eid = len(self._evidence)
        family = "reviewer" if "review" in source else "test"
        independent = family != candidate.last_modifier_family and (
            family == "test" or candidate.last_modifier_family != "reviewer"
        )
        record = EvidenceRecord(
            eid,
            action.candidate_id,
            candidate.public.version,
            source,
            family,
            flags,
            False,
            independent,
            True,
            self.elapsed,
        )
        self._evidence.append(record)
        return ActionOutcome(
            True, 0, 0, "evidence", action.candidate_id, candidate.public.version, eid
        )

    def _mutation(self, action: Action, usable: bool) -> ActionOutcome:
        if not usable:
            return ActionOutcome(False, 0, 0, "deadline")
        if action.candidate_id not in self._candidates or action.target_mode is None:
            return ActionOutcome(False, 0, 0, "missing_target")
        candidate = self._candidates[action.candidate_id]
        mode = action.target_mode
        agent = action.agent or "A2"
        changed: set[int] = set()
        explicitly_flagged = any(
            not e.stale
            and e.candidate_id == action.candidate_id
            and e.candidate_version == candidate.public.version
            and bool(e.flags[mode])
            for e in self._evidence
        )
        p_remove = expit(
            self.agent_world.competence[agent][mode]
            - self.task.difficulty[mode]
            + 0.8 * self.context_level
            - 0.4 * candidate.public.prior_repairs[mode]
            - BETA[action.kind] * self._n_eff(action)
        )
        if not explicitly_flagged:
            p_remove *= 0.5
        rng = self.rng.get("actual_agent_outcomes", len(self._actions), "repair", mode)
        if candidate.defects[mode] and rng.random() < p_remove:
            candidate.defects[mode] = False
            changed.add(mode)
        total_repairs = sum(candidate.public.prior_repairs)
        for k in range(5):
            if k == mode or candidate.defects[k]:
                continue
            if "regression_min" in self.regime:
                p_reg = rng.uniform(
                    float(self.regime["regression_min"]), float(self.regime["regression_max"])
                )
            else:
                p_reg = float(np.clip(BASE_REGRESSION[k] * (1 + 0.2 * total_repairs), 0, 0.25))
            if rng.random() < p_reg:
                candidate.defects[k] = True
                changed.add(k)
        candidate.public.prior_repairs[mode] += 1
        candidate.public.version += 1
        candidate.last_modifier_family = AGENT_FAMILY[agent]
        if self.invalidate_evidence:
            for evidence in self._evidence:
                if evidence.candidate_id == action.candidate_id and not evidence.stale:
                    evidence.stale = True
                    self.stale_invalidations += 1
        return ActionOutcome(
            True,
            0,
            0,
            "mutated",
            action.candidate_id,
            candidate.public.version,
            changed_modes=tuple(sorted(changed)),
        )

    def step(self, action: Action) -> ActionOutcome:
        if self.terminal is not None:
            self.post_terminal_attempts += 1
            return ActionOutcome(False, 0, 0, "terminal_absorbing")
        if action.kind == ActionType.ACCEPT:
            if action.candidate_id not in self._candidates:
                return ActionOutcome(False, 0, 0, "missing_candidate")
            self.terminal = TerminalDecision.ACCEPT
            self.accepted_candidate = action.candidate_id
            self.action_counts[action.kind.value] += 1
            return ActionOutcome(True, 0, 0, "accepted", action.candidate_id)
        if action.kind == ActionType.DECLARE_FAILURE:
            self.terminal = TerminalDecision.FAILURE
            self.action_counts[action.kind.value] += 1
            return ActionOutcome(True, 0, 0, "failure")
        cost, duration = self._sample_cost_duration(action)
        if self.spent + cost > self.task.budget + 1e-12:
            return ActionOutcome(False, 0, 0, "budget_rejected")
        self.spent += cost
        self.elapsed += duration
        if self.spent > self.task.budget + 1e-10:
            self.budget_violation = True
        usable = self.elapsed <= self.task.deadline
        if not usable:
            self.deadline_miss = True
        if action.kind in {
            ActionType.PRIMARY_GENERATION,
            ActionType.SAME_FAMILY_ALTERNATIVE,
            ActionType.DIVERSE_ALTERNATIVE,
        }:
            outcome = self._generation(action, usable)
        elif action.kind == ActionType.CONTEXT:
            outcome = self._context(action, usable)
        elif action.kind in VERIFICATION:
            outcome = self._verification(action, usable)
        elif action.kind in MUTATIONS:
            outcome = self._mutation(action, usable)
        else:
            outcome = ActionOutcome(False, 0, 0, "unsupported")
        self._actions.append(action)
        self.action_counts[action.kind.value] += 1
        return ActionOutcome(
            outcome.usable,
            cost,
            duration,
            outcome.reason,
            outcome.candidate_id,
            outcome.candidate_version,
            outcome.evidence_id,
            outcome.hints,
            outcome.changed_modes,
        )

    def _oracle_correct(self, candidate_id: int) -> bool:
        candidate = self._candidates[candidate_id]
        return not candidate.catastrophic and not bool(candidate.defects.any())

    def finalize(self, policy: str, seed: int, scheduler_seconds: float) -> EpisodeResult:
        if self.terminal is None:
            self.step(Action(ActionType.DECLARE_FAILURE))
        accepted = self.terminal == TerminalDecision.ACCEPT
        accepted_id = self.accepted_candidate
        correct = bool(accepted and accepted_id is not None and self._oracle_correct(accepted_id))
        severity = 0.0
        if accepted and not correct:
            assert accepted_id is not None
            cand = self._candidates[accepted_id]
            severity = float(np.dot(cand.defects.astype(float), SEVERITY))
            if cand.catastrophic:
                severity += 10.0
        return EpisodeResult(
            self.task.task_id,
            policy,
            self.regime_name,
            seed,
            accepted,
            correct,
            self.task.value,
            self.spent,
            self.elapsed,
            self.deadline_miss,
            self.budget_violation,
            scheduler_seconds,
            self.stale_invalidations,
            self.task.task_class,
            dict(self.action_counts),
            severity,
            self.post_terminal_attempts,
        )
