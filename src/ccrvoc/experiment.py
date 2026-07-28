from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ccrvoc.calibration import assert_no_test_leakage, calibrate_policy
from ccrvoc.causal_model import fit_propensity_weighted
from ccrvoc.environment import SequentialEnvironment
from ccrvoc.metrics import summarize
from ccrvoc.policies.base import BasePolicy
from ccrvoc.policies.ccr_voc import CCRVOCPolicy
from ccrvoc.policies.epsilon_bandit import EpsilonBanditPolicy
from ccrvoc.policies.fixed_compute import FixedComputePolicy
from ccrvoc.policies.fixed_retry import FixedRetryPolicy
from ccrvoc.policies.generate_review import GenerateReviewPolicy
from ccrvoc.policies.greedy_confidence import GreedyConfidencePolicy
from ccrvoc.policies.linucb import LinearThompsonPolicy, LinUCBPolicy
from ccrvoc.policies.macro import MacroPolicy
from ccrvoc.policies.thompson import ThompsonPolicy
from ccrvoc.policies.ucb import UCBPolicy
from ccrvoc.reporting import create_plots, write_report
from ccrvoc.rng import generator
from ccrvoc.runtime import execute_policy
from ccrvoc.statistics import clopper_pearson_upper, paired_bootstrap_relative_vud
from ccrvoc.tasks import generate_task


def _exploratory_logs(config: dict, ids: list[int]) -> pd.DataFrame:
    actions = list(config["action_means"])
    rows: list[dict] = []
    min_propensity = 1 / len(actions)
    for task_id in ids:
        task = generate_task(config["seed"], task_id, {})
        rng = generator(config["seed"], "causal_model_training", task_id)
        action_idx = int(rng.integers(len(actions)))
        action = actions[action_idx]
        value = task.value
        budget_remaining = task.budget * rng.uniform(0.25, 1)
        elapsed_fraction = rng.uniform(0, 0.8)
        evidence_count = int(rng.integers(0, 5))
        action_quality = 0.25 + 0.04 * action_idx
        logit_success = (
            -0.5
            + action_quality
            + 0.15 * value
            + 0.10 * budget_remaining
            - 0.8 * elapsed_fraction
            + 0.08 * evidence_count
            - 0.2 * float(task.difficulty.mean())
        )
        success = int(rng.random() < 1 / (1 + np.exp(-logit_success)))
        rows.append(
            {
                "task_id": task_id,
                "action": action,
                "propensity": min_propensity,
                "value": value,
                "budget_remaining": budget_remaining,
                "elapsed_fraction": elapsed_fraction,
                "evidence_count": evidence_count,
                "success": success,
                "stratum": task.task_class,
            }
        )
    return pd.DataFrame(rows)


def _factory(prototype: BasePolicy) -> Callable[[float], BasePolicy]:
    def build(threshold: float) -> BasePolicy:
        policy = deepcopy(prototype)
        policy.frozen = False
        policy.set_threshold(threshold)
        if isinstance(policy, CCRVOCPolicy):
            policy.beliefs = {}
            policy.processed_evidence = set()
            policy.candidate_versions = {}
            policy.repair_counts = {}
        return policy

    return build


def _run_tasks(
    config: dict,
    prototype: BasePolicy,
    task_ids: list[int],
    regime_name: str,
    regime: dict,
    seed: int,
    world: int,
    policy_name: str | None = None,
) -> list[dict]:
    rows: list[dict] = []
    for task_id in task_ids:
        env = SequentialEnvironment(
            config,
            task_id,
            regime_name,
            regime,
            world=world,
            invalidate_evidence=getattr(prototype, "ablation", None) != "no_evidence_invalidation",
        )
        policy = deepcopy(prototype)
        if isinstance(policy, CCRVOCPolicy):
            policy.beliefs = {}
            policy.processed_evidence = set()
            policy.candidate_versions = {}
            policy.repair_counts = {}
        result = execute_policy(policy, env, seed)
        row = result.as_dict()
        if policy_name:
            row["policy"] = policy_name
        for action, count in result.action_counts.items():
            row[f"action_{action}"] = count
        rows.append(row)
    return rows


def _train_bandit(
    config: dict, policy: MacroPolicy, task_ids: list[int], rho: float
) -> MacroPolicy:
    for task_id in task_ids:
        env = SequentialEnvironment(config, task_id, "training", {}, world=0)
        result = execute_policy(policy, env, seed=0)
        policy.observe_audited(result, rho)
    return policy


def _validation_tune_retries(config: dict, ids: list[int]) -> tuple[int, pd.DataFrame]:
    rows = []
    for retries in range(5):
        policy = FixedRetryPolicy(config, 0.05, retries)
        frame = pd.DataFrame(_run_tasks(config, policy, ids, "validation", {}, 0, 0))
        metrics = summarize(frame)
        rows.append({"retries": retries, **metrics})
    table = pd.DataFrame(rows)
    safeish = table[table["far"] <= 0.08]
    chosen = int(
        (safeish if not safeish.empty else table)
        .sort_values("vud", ascending=False)
        .iloc[0]["retries"]
    )
    return chosen, table


def _policy_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy, group in frame.groupby("policy"):
        row = {"policy": policy, **summarize(group)}
        row["far_upper_95"] = clopper_pearson_upper(
            int(row["false_accepts"]), int(row["accepted"]), 0.95
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _regime_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (policy, regime), group in frame.groupby(["policy", "regime"]):
        row = {"policy": policy, "regime": regime, **summarize(group)}
        row["far_upper_95"] = clopper_pearson_upper(
            int(row["false_accepts"]), int(row["accepted"]), 0.95
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _acceptance_evidence(
    config: dict,
    nominal: pd.DataFrame,
    policy_summary: pd.DataFrame,
    regime_summary: pd.DataFrame,
) -> tuple[dict, dict]:
    ccr = policy_summary[policy_summary.policy == "ccr_voc_learned"].iloc[0]
    baselines = policy_summary[
        ~policy_summary.policy.str.startswith("ccr_voc") & (policy_summary.far_upper_95 <= 0.05)
    ]
    strongest = (
        baselines.sort_values("vud", ascending=False).iloc[0] if not baselines.empty else None
    )
    rng = generator(config["seed"], "bootstrap_analysis", "acceptance")
    statistical: dict = {"strongest_safe_baseline": None}
    criteria: dict[str, dict[str, object]] = {}
    hard_far = float(ccr.far_upper_95) <= 0.05
    criteria["1 pooled FAR upper bound <= 0.05"] = {
        "pass": hard_far,
        "evidence": f"upper={ccr.far_upper_95:.6f}",
    }
    ccr_rows = nominal[nominal.policy == "ccr_voc_learned"]
    accepted = ccr_rows[ccr_rows.accepted]
    weighted = (
        float(accepted.severity_false_accept.sum() / max(len(accepted), 1))
        if len(accepted)
        else 0.0
    )
    boots = []
    if len(accepted):
        vals = accepted.severity_false_accept.to_numpy(float)
        for _ in range(2000):
            boots.append(float(rng.choice(vals, len(vals), replace=True).mean()))
    weighted_upper = float(np.quantile(boots, 0.95)) if boots else 1.0
    criteria["2 weighted FAR upper bound <= 0.05"] = {
        "pass": weighted_upper <= 0.05,
        "evidence": f"point={weighted:.6f}, bootstrap_upper={weighted_upper:.6f}",
    }
    if strongest is None:
        for number, text in [
            ("3", "absolute FAR increase upper <= 0.005"),
            ("5", "VUD point improvement >= 10%"),
            ("6", "paired-bootstrap relative VUD lower > 3%"),
            ("7", "correct utility not >2% below baseline"),
        ]:
            criteria[f"{number} {text}"] = {
                "pass": False,
                "evidence": "no baseline met final-test safety bound",
            }
    else:
        baseline_name = str(strongest.policy)
        statistical["strongest_safe_baseline"] = baseline_name
        b_rows = nominal[nominal.policy == baseline_name].sort_values(["regime", "seed", "task_id"])
        c_rows = ccr_rows.sort_values(["regime", "seed", "task_id"])
        n = min(len(b_rows), len(c_rows))
        c_false = (c_rows.accepted & ~c_rows.correct).to_numpy(float)[:n]
        b_false = (b_rows.accepted & ~b_rows.correct).to_numpy(float)[:n]
        diffs = []
        for _ in range(2000):
            idx = rng.integers(0, n, n)
            diffs.append(float((c_false[idx] - b_false[idx]).mean()))
        far_diff_upper = float(np.quantile(diffs, 0.95))
        criteria["3 absolute FAR increase upper <= 0.005"] = {
            "pass": far_diff_upper <= 0.005,
            "evidence": f"paired bootstrap upper={far_diff_upper:.6f} vs {baseline_name}",
        }
        rel = paired_bootstrap_relative_vud(
            c_rows.work.to_numpy(float)[:n],
            c_rows.cost.to_numpy(float)[:n],
            b_rows.work.to_numpy(float)[:n],
            b_rows.cost.to_numpy(float)[:n],
            rng,
        )
        statistical["relative_vud"] = {"point": rel[0], "lower": rel[1], "upper": rel[2]}
        criteria["5 VUD point improvement >= 10%"] = {
            "pass": rel[0] >= 0.10,
            "evidence": f"relative improvement={rel[0]:.6f}",
        }
        criteria["6 paired-bootstrap relative VUD lower > 3%"] = {
            "pass": rel[1] > 0.03,
            "evidence": f"95% interval=[{rel[1]:.6f}, {rel[2]:.6f}]",
        }
        utility_ratio = float(
            ccr.correct_utility_per_task / max(float(strongest.correct_utility_per_task), 1e-12)
        )
        criteria["7 correct utility not >2% below baseline"] = {
            "pass": utility_ratio >= 0.98,
            "evidence": f"ratio={utility_ratio:.6f}",
        }
    ccr_regimes = regime_summary[regime_summary.policy == "ccr_voc_learned"]
    criteria["4 no regime FAR upper bound > 0.10"] = {
        "pass": bool((ccr_regimes.far_upper_95 <= 0.10).all()),
        "evidence": f"maximum={ccr_regimes.far_upper_95.max():.6f}",
    }
    regime_passes = int(((ccr_regimes.far_upper_95 <= 0.05) & (ccr_regimes.vud > 0)).sum())
    pooled = all(
        bool(criteria[key]["pass"])
        for key in [
            "1 pooled FAR upper bound <= 0.05",
            "2 weighted FAR upper bound <= 0.05",
        ]
    )
    criteria["8 pooled and at least four regimes"] = {
        "pass": pooled and regime_passes >= 4,
        "evidence": f"regimes={regime_passes}/6",
    }
    criteria["9 budget violation exactly zero"] = {
        "pass": bool((ccr_rows.budget_violation == 0).all()),
        "evidence": f"violations={int(ccr_rows.budget_violation.sum())}",
    }
    criteria["10 no actions after terminal"] = {
        "pass": bool((ccr_rows.terminal_action_count == 0).all()),
        "evidence": f"attempts={int(ccr_rows.terminal_action_count.sum())}",
    }
    overhead_dollars = float(ccr.scheduler_overhead_seconds) * 0.0001
    total_cost = float(ccr_rows.cost.sum())
    overhead_fraction = overhead_dollars / max(total_cost, 1e-12)
    criteria["11 scheduler overhead <=10% cost"] = {
        "pass": overhead_fraction <= 0.10,
        "evidence": f"assumption=$0.0001/s, fraction={overhead_fraction:.6f}",
    }
    acceptance = {
        "mode": config["mode"],
        "criteria": criteria,
        "all_hard_risk": all(bool(criteria[k]["pass"]) for k in list(criteria)[:4]),
    }
    return acceptance, statistical


def run_experiment(config: dict, output: str | Path) -> str:
    start = time.time()
    artifacts = Path(output)
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "config_resolved.yaml").write_text(yaml.safe_dump(config, sort_keys=True))
    sizes = config["sizes"]
    train_ids = list(range(0, sizes["training"]))
    validation_ids = list(range(1_000_000, 1_000_000 + sizes["validation"]))
    calibration_ids = list(range(2_000_000, 2_000_000 + sizes["calibration"]))

    logs = _exploratory_logs(config, train_ids)
    causal = fit_propensity_weighted(logs)
    causal.freeze()
    overlap = causal.diagnostics.as_dict()
    (artifacts / "overlap_diagnostics.json").write_text(json.dumps(overlap, indent=2))
    chosen_retries, validation_table = _validation_tune_retries(config, validation_ids)

    prototypes: dict[str, BasePolicy] = {
        "ccr_voc_learned": CCRVOCPolicy(config, model_mode="learned_model", causal_model=causal),
        "ccr_voc_known": CCRVOCPolicy(config, model_mode="known_model"),
        "fixed_compute": FixedComputePolicy(config),
        "fixed_retry": FixedRetryPolicy(config, retries=chosen_retries),
        "generate_review": GenerateReviewPolicy(config),
        "greedy_confidence": GreedyConfidencePolicy(config),
        "epsilon_bandit": EpsilonBanditPolicy(config),
        "thompson": ThompsonPolicy(config),
        "ucb1": UCBPolicy(config),
        "linear_thompson": LinearThompsonPolicy(config),
        "linucb": LinUCBPolicy(config),
    }
    for name in ["epsilon_bandit", "thompson", "ucb1", "linear_thompson", "linucb"]:
        bandit = prototypes[name]
        assert isinstance(bandit, MacroPolicy)
        prototypes[name] = _train_bandit(config, bandit, train_ids, float(config["rho"]))
    training_diag = {
        "training_tasks": len(train_ids),
        "validation_tasks": len(validation_ids),
        "chosen_fixed_retries": chosen_retries,
        "validation_tuning": validation_table.to_dict(orient="records"),
        "causal_estimator": "inverse-propensity-weighted logistic regression",
        "runtime_seconds_before_calibration": time.time() - start,
    }
    (artifacts / "training_diagnostics.json").write_text(json.dumps(training_diag, indent=2))

    calibration_tables = []
    frozen = {}
    for name, prototype in prototypes.items():
        selection, table = calibrate_policy(config, _factory(prototype), name, calibration_ids)
        assert_no_test_leakage(
            selection,
            set(train_ids),
            set(validation_ids),
            set(),
        )
        prototype.set_threshold(selection.threshold)
        prototype.freeze()
        frozen[name] = selection
        calibration_tables.append(table)
    calibration = pd.concat(calibration_tables, ignore_index=True)
    calibration.to_csv(artifacts / "calibration_results.csv", index=False)

    nominal_rows: list[dict] = []
    nominal_test_ids: set[int] = set()
    for regime_idx, (regime_name, regime) in enumerate(config["regimes"].items()):
        for seed in range(sizes["nominal_seeds"]):
            base = 3_000_000 + regime_idx * 100_000 + seed * 10_000
            ids = list(range(base, base + sizes["nominal_tasks_per_seed"]))
            nominal_test_ids.update(ids)
            for name, prototype in prototypes.items():
                nominal_rows.extend(
                    _run_tasks(config, prototype, ids, regime_name, regime, seed, seed, name)
                )
    for selection in frozen.values():
        assert_no_test_leakage(
            selection,
            set(train_ids),
            set(validation_ids),
            nominal_test_ids,
        )
    nominal = pd.DataFrame(nominal_rows).fillna(0)
    nominal.to_parquet(artifacts / "nominal_task_results.parquet", index=False)

    adversarial_rows: list[dict] = []
    for regime_idx, (regime_name, regime) in enumerate(config["adversarial_regimes"].items()):
        for seed in range(sizes["adversarial_seeds"]):
            base = 10_000_000 + regime_idx * 100_000 + seed * 10_000
            ids = list(range(base, base + sizes["adversarial_tasks_per_seed"]))
            for name, prototype in prototypes.items():
                adversarial_rows.extend(
                    _run_tasks(config, prototype, ids, regime_name, regime, seed, seed, name)
                )
    adversarial = pd.DataFrame(adversarial_rows).fillna(0)
    adversarial.to_parquet(artifacts / "adversarial_task_results.parquet", index=False)

    policy_summary = _policy_summary(nominal)
    policy_summary.to_csv(artifacts / "policy_summary.csv", index=False)
    combined = pd.concat([nominal, adversarial], ignore_index=True)
    regime_summary = _regime_summary(combined)
    regime_summary.to_csv(artifacts / "regime_summary.csv", index=False)

    ablation_rows: list[dict] = []
    ablation_ids = list(range(20_000_000, 20_000_000 + sizes["nominal_tasks_per_seed"]))
    learned_threshold = frozen["ccr_voc_learned"].threshold
    for ablation in config["ablations"]:
        policy = CCRVOCPolicy(
            config,
            learned_threshold if ablation != "uncalibrated_threshold" else 0.05,
            ablation,
            "learned_model",
            causal,
        )
        frame = pd.DataFrame(_run_tasks(config, policy, ablation_ids, "balanced_default", {}, 0, 0))
        ablation_rows.append({"ablation": ablation, **summarize(frame)})
    ablation_summary = pd.DataFrame(ablation_rows)
    ablation_summary.to_csv(artifacts / "ablation_summary.csv", index=False)

    acceptance, statistical = _acceptance_evidence(config, nominal, policy_summary, regime_summary)
    statistical["common_random_numbers"] = True
    statistical["bootstrap_replicates"] = 2000
    (artifacts / "statistical_tests.json").write_text(json.dumps(statistical, indent=2))
    status = "PARTIAL"
    if config["mode"] == "full":
        passes = [bool(item["pass"]) for item in acceptance["criteria"].values()]
        if all(passes):
            status = "PASS"
        elif acceptance["all_hard_risk"] and sum(not p for p in passes) == 1:
            status = "PASS_WITH_WARNINGS"
        else:
            status = "FAIL"
    acceptance["status"] = status
    acceptance["elapsed_seconds"] = time.time() - start
    (artifacts / "acceptance_checklist.json").write_text(json.dumps(acceptance, indent=2))
    create_plots(artifacts, calibration, nominal, policy_summary, regime_summary)
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_hash = "UNCOMMITTED"
    commands = [
        "uv sync --extra dev",
        "uv run pytest",
        "uv run ruff check .",
        "uv run mypy src",
        f"uv run ccrvoc run --config configs/{config['mode']}.yaml --output artifacts",
    ]
    test_summary = (
        (artifacts / "test_results.txt").read_text()
        if (artifacts / "test_results.txt").exists()
        else "Test output was not supplied to the experiment runner."
    )
    write_report(
        artifacts,
        config,
        commit_hash,
        commands,
        test_summary,
        policy_summary,
        regime_summary,
        calibration,
        overlap,
        acceptance,
        status,
    )
    return status


def finalize_existing(
    config: dict,
    output: str | Path,
    executed_commit: str,
) -> str:
    """Recover deterministic reporting from already-completed task-level artifacts."""
    artifacts = Path(output)
    calibration = pd.read_csv(artifacts / "calibration_results.csv")
    nominal = pd.read_parquet(artifacts / "nominal_task_results.parquet")
    policy_summary = pd.read_csv(artifacts / "policy_summary.csv")
    regime_summary = pd.read_csv(artifacts / "regime_summary.csv")
    overlap = json.loads((artifacts / "overlap_diagnostics.json").read_text())
    acceptance = json.loads((artifacts / "acceptance_checklist.json").read_text())
    status = str(acceptance["status"])
    create_plots(artifacts, calibration, nominal, policy_summary, regime_summary)
    commands = [
        "UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv sync --extra dev",
        "UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run pytest",
        "UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run ruff check .",
        "UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run mypy src",
        "GIT_DIR=.ccrvoc-git GIT_WORK_TREE=. UV_CACHE_DIR=/tmp/ccrvoc-uv-cache "
        f"uv run ccrvoc run --config configs/{config['mode']}.yaml --output artifacts",
        "UV_CACHE_DIR=/tmp/ccrvoc-uv-cache MPLCONFIGDIR=/tmp/ccrvoc-matplotlib "
        f"uv run ccrvoc finalize --config configs/{config['mode']}.yaml "
        f"--output artifacts --executed-commit {executed_commit}",
    ]
    test_summary = (artifacts / "test_results.txt").read_text()
    write_report(
        artifacts,
        config,
        executed_commit,
        commands,
        test_summary,
        policy_summary,
        regime_summary,
        calibration,
        overlap,
        acceptance,
        status,
    )
    return status
