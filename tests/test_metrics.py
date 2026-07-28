import pandas as pd

from ccrvoc.metrics import summarize


def test_metrics_handle_zero_accepted() -> None:
    rows = pd.DataFrame(
        [
            {
                "accepted": False,
                "correct": False,
                "cost": 1.0,
                "work": 0.0,
                "severity_false_accept": 0.0,
                "deadline_miss": False,
                "budget_violation": False,
                "scheduler_seconds": 0.0,
                "stale_invalidations": 0,
            }
        ]
    )
    metrics = summarize(rows)
    assert metrics["far"] == 0
    assert metrics["acceptance_coverage"] == 0
