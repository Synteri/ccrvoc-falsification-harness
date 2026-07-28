from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from ccrvoc.environment import SequentialEnvironment
from ccrvoc.metrics import summarize
from ccrvoc.policies.base import BasePolicy
from ccrvoc.runtime import execute_policy
from ccrvoc.statistics import clopper_pearson_upper


@dataclass(frozen=True)
class FrozenCalibration:
    policy_name: str
    threshold: float
    calibration_fingerprint: tuple[int, ...]
    confidence: float
    safe: bool


def calibrate_policy(
    config: dict,
    policy_factory: Callable[[float], BasePolicy],
    policy_name: str,
    task_ids: list[int],
    regime_name: str = "balanced_default",
    regime: dict | None = None,
) -> tuple[FrozenCalibration, pd.DataFrame]:
    thresholds = list(config["risk_threshold_grid"])
    confidence = 1 - 0.05 / len(thresholds)
    rows: list[dict] = []
    for threshold in thresholds:
        results = []
        for task_id in task_ids:
            env = SequentialEnvironment(config, task_id, regime_name, regime or {}, world=0)
            policy = policy_factory(float(threshold))
            results.append(execute_policy(policy, env, seed=0).as_dict())
        frame = pd.DataFrame(results)
        metrics = summarize(frame)
        accepted = int(metrics["accepted"])
        errors = int(metrics["false_accepts"])
        upper = clopper_pearson_upper(errors, accepted, confidence)
        rows.append(
            {
                "policy": policy_name,
                "threshold": threshold,
                "tasks": len(task_ids),
                "accepted": accepted,
                "incorrect": errors,
                "far": metrics["far"],
                "far_upper_bonferroni": upper,
                "vud": metrics["vud"],
                "safe": upper <= 0.05,
                "split": "calibration",
            }
        )
    table = pd.DataFrame(rows)
    safe = table[table["safe"]]
    if safe.empty:
        chosen = table.sort_values(["far_upper_bonferroni", "vud"], ascending=[True, False]).iloc[0]
        is_safe = False
    else:
        chosen = safe.sort_values("vud", ascending=False).iloc[0]
        is_safe = True
    frozen = FrozenCalibration(
        policy_name,
        float(chosen["threshold"]),
        tuple(task_ids),
        confidence,
        is_safe,
    )
    return frozen, table


def assert_no_test_leakage(
    calibration: FrozenCalibration,
    training_ids: set[int],
    validation_ids: set[int],
    test_ids: set[int],
) -> None:
    calibration_ids = set(calibration.calibration_fingerprint)
    if calibration_ids & training_ids:
        raise AssertionError("calibration overlaps training")
    if calibration_ids & validation_ids:
        raise AssertionError("calibration overlaps validation")
    if calibration_ids & test_ids:
        raise AssertionError("test labels affected calibration")
