from __future__ import annotations

from typing import Any

import numpy as np

from ccrvoc.actions import candidate_actions
from ccrvoc.belief import ParticleBelief, evidence_is_acceptance_eligible
from ccrvoc.policies.base import BasePolicy
from ccrvoc.types import Action, ActionType, PolicyView


class CCRVOCPolicy(BasePolicy):
    name = "ccr_voc"

    def __init__(
        self,
        config: dict,
        risk_threshold: float = 0.05,
        ablation: str | None = None,
        model_mode: str = "learned_model",
        causal_model: Any | None = None,
    ) -> None:
        super().__init__(config, risk_threshold)
        self.ablation = ablation
        self.model_mode = model_mode
        self.causal_model = causal_model
        self.beliefs: dict[int, ParticleBelief] = {}
        self.processed_evidence: set[int] = set()
        self.depth = (
            1 if ablation == "h1" else 3 if ablation == "h3" else int(config["planning_depth"])
        )

    def clone(self) -> CCRVOCPolicy:
        return type(self)(
            self.config,
            self.risk_threshold,
            self.ablation,
            self.model_mode,
            self.causal_model,
        )

    def _sync(self, view: PolicyView) -> None:
        for candidate in view.candidates:
            if candidate.candidate_id not in self.beliefs:
                prior = float(np.clip(0.30 * np.exp(-0.8 * candidate.context_level), 0.02, 0.8))
                self.beliefs[candidate.candidate_id] = ParticleBelief.initialize(
                    self.config, view.task.task_id * 101 + candidate.candidate_id, prior
                )
        for evidence in view.evidence:
            if evidence.evidence_id in self.processed_evidence or evidence.stale:
                continue
            matched_candidate = next(
                (c for c in view.candidates if c.candidate_id == evidence.candidate_id), None
            )
            if matched_candidate is None or matched_candidate.version != evidence.candidate_version:
                continue
            repeated = sum(
                1
                for old in view.evidence
                if old.evidence_id < evidence.evidence_id
                and old.source == evidence.source
                and old.candidate_id == evidence.candidate_id
                and not old.stale
            )
            belief = self.beliefs[evidence.candidate_id]
            if self.ablation == "no_correlation":
                repeated = 0
            belief.update_evidence(evidence, repeated)
            self.processed_evidence.add(evidence.evidence_id)

    def risk_score(self, view: PolicyView, candidate_id: int) -> float:
        self._sync(view)
        belief = self.beliefs[candidate_id]
        quantile = 0.50 if self.ablation == "posterior_mean" else 0.95
        return belief.robust_risk(quantile)

    def _terminal_value(self, view: PolicyView) -> float:
        values = []
        for candidate in view.candidates:
            if not evidence_is_acceptance_eligible(view, candidate.candidate_id):
                continue
            risk = self.risk_score(view, candidate.candidate_id)
            if risk <= self.risk_threshold:
                values.append(view.task.value * (1 - risk))
        return max(values, default=0.0)

    def _model_q(self, view: PolicyView, action: Action) -> np.ndarray:
        members = int(self.config["ensemble_members"])
        mean_cost = self.config["action_means"][action.kind.value]["cost"]
        mean_time = self.config["action_means"][action.kind.value]["seconds"]
        rho = float(self.config["rho"])
        base = -rho * mean_cost - float(self.config["lambda_time"]) * mean_time
        causal_factor = 1.0
        if self.model_mode == "learned_model" and self.causal_model is not None:
            features = np.array(
                [
                    view.task.value,
                    view.task.budget - view.spent,
                    view.elapsed / max(view.task.deadline, 1),
                    len([e for e in view.evidence if not e.stale]),
                ]
            )
            causal_factor = 0.5 + float(
                self.causal_model.predict_success(action.kind.value, features)
            )
        if action.kind in {
            ActionType.PRIMARY_GENERATION,
            ActionType.SAME_FAMILY_ALTERNATIVE,
            ActionType.DIVERSE_ALTERNATIVE,
        }:
            quality = {
                ActionType.PRIMARY_GENERATION: 0.35,
                ActionType.SAME_FAMILY_ALTERNATIVE: 0.40,
                ActionType.DIVERSE_ALTERNATIVE: 0.52,
            }[action.kind]
            gain = view.task.value * quality * causal_factor
        elif action.kind == ActionType.CONTEXT:
            gain = view.task.value * 0.10 * (1 - view.context_level) * causal_factor
        elif action.kind in {
            ActionType.UNIT_TEST,
            ActionType.INTEGRATION_TEST,
            ActionType.FUZZ_SECURITY,
            ActionType.INDEPENDENT_REVIEW,
            ActionType.ADVERSARIAL_REVIEW,
            ActionType.REVIEWER_RERUN,
        }:
            current = (
                self.beliefs[action.candidate_id].risk_by_ensemble()
                if action.candidate_id in self.beliefs
                else np.full(members, 0.8)
            )
            info = {
                ActionType.UNIT_TEST: 0.20,
                ActionType.INTEGRATION_TEST: 0.25,
                ActionType.FUZZ_SECURITY: 0.25,
                ActionType.INDEPENDENT_REVIEW: 0.35,
                ActionType.ADVERSARIAL_REVIEW: 0.40,
                ActionType.REVIEWER_RERUN: 0.12,
            }[action.kind]
            gain_by_member = view.task.value * info * current * causal_factor
            if self.depth > 1:
                gain_by_member *= 1 + 0.20 * (self.depth - 1)
            return base + gain_by_member
        elif action.kind in {ActionType.REPAIR, ActionType.DEBUG}:
            current = (
                self.beliefs[action.candidate_id].risk_by_ensemble()
                if action.candidate_id in self.beliefs
                else np.full(members, 0.8)
            )
            return base + view.task.value * 0.30 * current * causal_factor
        else:
            gain = 0.0
        if self.depth > 1:
            gain *= 1 + 0.10 * (self.depth - 1)
        spread = np.linspace(0.85, 1.15, members)
        return base + gain * spread

    def choose_action(self, view: PolicyView) -> Action:
        self._sync(view)
        safe = self.safe_candidate(view)
        if safe is not None:
            return Action(ActionType.ACCEPT, safe)
        if sum(view.action_counts.values()) >= 12:
            return Action(ActionType.DECLARE_FAILURE)
        feasible = []
        for action in candidate_actions(view):
            means = self.config["action_means"].get(action.kind.value)
            if means and view.spent + means["cost"] <= view.task.budget:
                feasible.append(action)
        if not feasible:
            return Action(ActionType.DECLARE_FAILURE)
        v0 = self._terminal_value(view)
        scores: list[tuple[float, Action]] = []
        for action in feasible:
            q = self._model_q(view, action)
            conservative = float(
                np.mean(q) if self.ablation == "posterior_mean" else np.quantile(q, 0.10)
            )
            scores.append((conservative - v0, action))
        voc, best = max(scores, key=lambda pair: pair[0])
        if voc > float(self.config["epsilon_voc_fraction"]) * view.task.value:
            return best
        return Action(ActionType.DECLARE_FAILURE)
