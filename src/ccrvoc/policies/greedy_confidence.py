from __future__ import annotations

import numpy as np

from ccrvoc.actions import candidate_actions
from ccrvoc.evidence import FALSE_POSITIVE, SENSITIVITY
from ccrvoc.policies.base import BasePolicy
from ccrvoc.types import Action, ActionType, PolicyView


class GreedyConfidencePolicy(BasePolicy):
    name = "greedy_confidence"

    def choose_action(self, view: PolicyView) -> Action:
        safe = self.safe_candidate(view)
        if safe is not None:
            return Action(ActionType.ACCEPT, safe)
        if sum(view.action_counts.values()) >= 9:
            return Action(ActionType.DECLARE_FAILURE)
        if not view.candidates:
            return Action(ActionType.PRIMARY_GENERATION, agent="A2")
        actions = candidate_actions(view)
        feasible = [
            a
            for a in actions
            if a.kind.value in self.config["action_means"]
            and view.spent + self.config["action_means"][a.kind.value]["cost"] <= view.task.budget
        ]
        if not feasible:
            return Action(ActionType.DECLARE_FAILURE)
        candidate = view.candidates[-1]
        candidate_id = candidate.candidate_id
        p = self.mode_probabilities(view, candidate_id)
        current_risk = float(1 - np.prod(1 - p))
        source_counts: dict[str, int] = {}
        for evidence in view.evidence:
            if (
                not evidence.stale
                and evidence.candidate_id == candidate_id
                and evidence.candidate_version == candidate.version
            ):
                source_counts[evidence.source] = source_counts.get(evidence.source, 0) + 1

        def score(action: Action) -> float:
            cost = float(self.config["action_means"][action.kind.value]["cost"])
            if action.source in SENSITIVITY:
                source = action.source
                sensitivity = SENSITIVITY[source]
                fpr = FALSE_POSITIVE[source]
                repeat = source_counts.get(source, 0)
                discount = 1.0 if repeat == 0 else 0.35
                odds = p / np.maximum(1 - p, 1e-12)
                negative_ratio = (1 - sensitivity) / (1 - fpr)
                negative_odds = odds * np.power(negative_ratio, discount)
                p_negative = negative_odds / (1 + negative_odds)
                negative_risk = float(1 - np.prod(1 - p_negative))
                detection_probability = float(np.mean(p * sensitivity + (1 - p) * fpr))
                information = current_risk - negative_risk + 0.15 * detection_probability
                return information / cost
            if action.kind == ActionType.REPAIR and action.target_mode is not None:
                return float(0.5 * p[action.target_mode] / cost)
            if action.kind == ActionType.CONTEXT:
                return float(0.08 * current_risk * (1 - view.context_level) / cost)
            if action.kind in {
                ActionType.SAME_FAMILY_ALTERNATIVE,
                ActionType.DIVERSE_ALTERNATIVE,
            }:
                return 0.03 / cost
            return 0.0

        return max(feasible, key=score)
