from __future__ import annotations

from ccrvoc.actions import candidate_actions
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
        information = {
            ActionType.UNIT_TEST: 0.45,
            ActionType.INTEGRATION_TEST: 0.55,
            ActionType.FUZZ_SECURITY: 0.50,
            ActionType.INDEPENDENT_REVIEW: 0.65,
            ActionType.ADVERSARIAL_REVIEW: 0.70,
            ActionType.CONTEXT: 0.15,
            ActionType.SAME_FAMILY_ALTERNATIVE: 0.20,
            ActionType.DIVERSE_ALTERNATIVE: 0.35,
            ActionType.REPAIR: 0.50,
        }
        feasible = [
            a
            for a in actions
            if a.kind.value in self.config["action_means"]
            and view.spent + self.config["action_means"][a.kind.value]["cost"] <= view.task.budget
        ]
        if not feasible:
            return Action(ActionType.DECLARE_FAILURE)
        return max(
            feasible,
            key=lambda a: (
                information.get(a.kind, 0) / self.config["action_means"][a.kind.value]["cost"]
            ),
        )
