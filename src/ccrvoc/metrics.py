from __future__ import annotations

import pandas as pd


def summarize(rows: pd.DataFrame) -> dict[str, float]:
    if rows.empty:
        return {key: 0.0 for key in _METRIC_KEYS}
    accepted = rows["accepted"].astype(bool)
    correct = rows["correct"].astype(bool)
    false = accepted & ~correct
    total_cost = float(rows["cost"].sum())
    correct_count = int((accepted & correct).sum())
    return {
        "vud": float(rows["work"].sum() / max(total_cost, 1e-12)),
        "correct_utility_per_task": float(rows["work"].sum() / len(rows)),
        "far": float(false.sum() / max(int(accepted.sum()), 1)),
        "severity_weighted_far": float(
            rows.loc[false, "severity_false_accept"].sum()
            / max(float(rows.loc[accepted, "severity_false_accept"].sum() + accepted.sum()), 1)
        ),
        "acceptance_coverage": float(accepted.mean()),
        "correct_acceptance_rate": float((accepted & correct).mean()),
        "failure_declaration_rate": float((~accepted).mean()),
        "cost_per_task": float(total_cost / len(rows)),
        "cost_per_correct_task": float(total_cost / max(correct_count, 1)),
        "deadline_miss_rate": float(rows["deadline_miss"].mean()),
        "budget_violation_rate": float(rows["budget_violation"].mean()),
        "scheduler_overhead_seconds": float(rows["scheduler_seconds"].sum()),
        "stale_evidence_invalidations": float(rows["stale_invalidations"].sum()),
        "accepted": float(accepted.sum()),
        "false_accepts": float(false.sum()),
        "tasks": float(len(rows)),
    }


_METRIC_KEYS = [
    "vud",
    "correct_utility_per_task",
    "far",
    "severity_weighted_far",
    "acceptance_coverage",
    "correct_acceptance_rate",
    "failure_declaration_rate",
    "cost_per_task",
    "cost_per_correct_task",
    "deadline_miss_rate",
    "budget_violation_rate",
    "scheduler_overhead_seconds",
    "stale_evidence_invalidations",
    "accepted",
    "false_accepts",
    "tasks",
]
