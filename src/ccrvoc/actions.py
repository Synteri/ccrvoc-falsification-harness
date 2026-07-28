from __future__ import annotations

from ccrvoc.types import Action, ActionType, PolicyView

VERIFICATION = {
    ActionType.UNIT_TEST,
    ActionType.INTEGRATION_TEST,
    ActionType.FUZZ_SECURITY,
    ActionType.INDEPENDENT_REVIEW,
    ActionType.ADVERSARIAL_REVIEW,
    ActionType.REVIEWER_RERUN,
}
MUTATIONS = {ActionType.DEBUG, ActionType.REPAIR}


def candidate_actions(view: PolicyView) -> list[Action]:
    if view.terminal:
        return []
    actions: list[Action] = []
    if not view.candidates:
        actions.extend(
            [
                Action(ActionType.CONTEXT),
                Action(ActionType.PRIMARY_GENERATION, agent="A0"),
                Action(ActionType.PRIMARY_GENERATION, agent="A2"),
            ]
        )
        return actions
    c = view.candidates[-1]
    current_evidence = [
        evidence
        for evidence in view.evidence
        if not evidence.stale
        and evidence.candidate_id == c.candidate_id
        and evidence.candidate_version == c.version
    ]
    actions.extend(
        [
            Action(ActionType.CONTEXT),
            Action(ActionType.UNIT_TEST, c.candidate_id, "unit_test"),
            Action(ActionType.INTEGRATION_TEST, c.candidate_id, "integration_test"),
            Action(ActionType.FUZZ_SECURITY, c.candidate_id, "fuzz_security"),
            Action(
                ActionType.INDEPENDENT_REVIEW,
                c.candidate_id,
                "independent_review",
            ),
            Action(
                ActionType.INDEPENDENT_REVIEW,
                c.candidate_id,
                "spec_review",
            ),
            Action(
                ActionType.ADVERSARIAL_REVIEW,
                c.candidate_id,
                "adversarial_review",
            ),
        ]
    )
    if len(current_evidence) >= 2 or any(evidence.flags.any() for evidence in current_evidence):
        actions.extend(
            [
                Action(ActionType.SAME_FAMILY_ALTERNATIVE, agent="A1"),
                Action(ActionType.DIVERSE_ALTERNATIVE, agent="A2"),
            ]
        )
    flags = [evidence.flags for evidence in current_evidence]
    if flags:
        for mode in range(5):
            if any(bool(f[mode]) for f in flags):
                actions.append(
                    Action(ActionType.REPAIR, c.candidate_id, agent="A2", target_mode=mode)
                )
    return actions


def similarity(action: Action, prior: Action) -> float:
    if (
        action.kind == prior.kind
        and action.source == prior.source
        and action.candidate_id == prior.candidate_id
    ):
        return 1.0
    if action.kind == prior.kind and action.source != prior.source:
        return 0.3
    review = {
        ActionType.INDEPENDENT_REVIEW,
        ActionType.ADVERSARIAL_REVIEW,
        ActionType.REVIEWER_RERUN,
    }
    if action.kind in review and prior.kind in review:
        return 0.7
    return 0.0
