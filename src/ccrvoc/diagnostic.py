from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import cast

import pandas as pd
import yaml

from ccrvoc.calibration import assert_no_test_leakage, calibrate_policy
from ccrvoc.causal_model import fit_propensity_weighted
from ccrvoc.experiment import _exploratory_logs, _factory, _policy_summary, _run_tasks
from ccrvoc.policies.base import BasePolicy
from ccrvoc.policies.ccr_voc import CCRVOCPolicy
from ccrvoc.policies.fixed_compute import FixedComputePolicy
from ccrvoc.policies.greedy_confidence import GreedyConfidencePolicy


def evaluate_diagnostic_gates(
    calibration: pd.DataFrame,
    summary: pd.DataFrame,
    chosen: dict[str, dict[str, object]],
    minimum_acceptances: int = 100,
) -> dict[str, dict[str, object]]:
    serious = tuple(chosen)
    baseline_names = {"fixed_compute", "greedy_confidence"}
    selected_acceptances = {
        name: int(
            calibration[
                (calibration["policy"] == name)
                & (calibration["threshold"] == cast(float, record["threshold"]))
            ].iloc[0]["accepted"]
        )
        for name, record in chosen.items()
    }
    safe_baselines = [
        name for name, record in chosen.items() if name in baseline_names and bool(record["safe"])
    ]
    vud = {
        str(row.policy): float(row.vud)
        for row in summary.itertuples()
        if str(row.policy) in serious
    }
    invariants = {
        "budget_violations": int(summary["budget_violation_rate"].gt(0).sum()),
        "post_terminal_attempts": int(summary.get("terminal_action_count", pd.Series([0])).sum()),
    }
    return {
        "calibration_acceptance_support": {
            "pass": all(value >= minimum_acceptances for value in selected_acceptances.values()),
            "required_per_policy": minimum_acceptances,
            "selected_acceptances": selected_acceptances,
        },
        "safe_baseline_exists": {
            "pass": bool(safe_baselines),
            "safe_baselines": safe_baselines,
        },
        "nonzero_vud": {
            "pass": all(vud.get(name, 0.0) > 0 for name in serious),
            "vud": vud,
        },
        "risk_calibration": {
            "pass": all(bool(record["safe"]) for record in chosen.values()),
            "selected_policy_calibrations": chosen,
        },
        "budget_and_terminal_invariants": {
            "pass": invariants["budget_violations"] == 0
            and invariants["post_terminal_attempts"] == 0,
            **invariants,
        },
    }


def _report(
    commit: str,
    elapsed: float,
    config: dict,
    calibration: pd.DataFrame,
    summary: pd.DataFrame,
    chosen: dict[str, dict[str, object]],
    gates: dict[str, dict[str, object]],
) -> str:
    calibration_lines = calibration.to_csv(index=False)
    summary_lines = summary.to_csv(index=False)
    gate_lines = "\n".join(
        f"- {'PASS' if item['pass'] else 'FAIL'} — {name}: `{json.dumps(item, sort_keys=True)}`"
        for name, item in gates.items()
    )
    authorized = all(bool(item["pass"]) for item in gates.values())
    authorization_word = "authorized" if authorized else "not authorized"
    return f"""# CCR-VOC bounded repair diagnostic

## Outcome

The bounded repair diagnostic {"passed" if authorized else "did not pass"} its gates.
Accordingly, a second fast or full experiment is **{authorization_word}**.
This diagnostic is not a validation of the master hypothesis.

## Reproducibility

- Commit: `{commit}`
- Command:
  `UV_CACHE_DIR=/tmp/ccrvoc-repair-uv MPLCONFIGDIR=/tmp/ccrvoc-mpl`
  `uv run ccrvoc diagnostic --config configs/diagnostic.yaml`
  `--output artifacts/repair_diagnostic`
- Elapsed seconds: {elapsed:.3f}
- Resolved diagnostic sizes: `{json.dumps(config["diagnostic_sizes"], sort_keys=True)}`
- Threshold grid: `{json.dumps(config["risk_threshold_grid"])}`
- Estimator: inverse-propensity-weighted logistic transition model

## Frozen calibration choices

```json
{json.dumps(chosen, indent=2, sort_keys=True)}
```

## Gates

{gate_lines}

## Calibration results

```csv
{calibration_lines}```

## Disjoint-test policy summary

```csv
{summary_lines}```

## Interpretation

The repair removed a schedule-cursor defect, exposed specification review, prevented stale
evidence from remaining in the particle posterior after mutations, and corrected an
overvaluation of alternative generation. Controlled fixtures now demonstrate that clean,
independent evidence can cross the acceptance threshold and that mode-specific warnings block
acceptance.

The end-to-end trajectories remain the decisive evidence. Any failed gate above blocks further
scale-up. In particular, zero acceptance is not evidence of a safe selective policy: its
Clopper–Pearson upper bound is 1 when there are no accepted trials. Likewise, a high-VUD policy is
not a safe baseline unless its calibrated upper bound is at most 0.05.

## Status

PARTIAL
"""


def run_diagnostic(config: dict, output: str | Path) -> str:
    start = time.time()
    artifacts = Path(output)
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "config_resolved.yaml").write_text(yaml.safe_dump(config, sort_keys=True))
    sizes = config["diagnostic_sizes"]
    training_ids = list(range(30_000_000, 30_000_000 + int(sizes["training"])))
    calibration_ids = list(range(31_000_000, 31_000_000 + int(sizes["calibration"])))
    test_ids = list(range(32_000_000, 32_000_000 + int(sizes["test"])))

    logs = _exploratory_logs(config, training_ids)
    causal = fit_propensity_weighted(logs)
    causal.freeze()
    overlap = causal.diagnostics.as_dict()
    (artifacts / "overlap_diagnostics.json").write_text(json.dumps(overlap, indent=2))

    prototypes: dict[str, BasePolicy] = {
        "fixed_compute": FixedComputePolicy(config),
        "greedy_confidence": GreedyConfidencePolicy(config),
        "ccr_voc_known": CCRVOCPolicy(config, model_mode="known_model"),
        "ccr_voc_learned": CCRVOCPolicy(
            config,
            model_mode="learned_model",
            causal_model=causal,
        ),
    }
    tables: list[pd.DataFrame] = []
    selections: dict[str, dict[str, object]] = {}
    for name, prototype in prototypes.items():
        print(f"calibrating {name}", flush=True)
        selection, table = calibrate_policy(
            config,
            _factory(prototype),
            name,
            calibration_ids,
        )
        assert_no_test_leakage(
            selection,
            set(training_ids),
            set(),
            set(test_ids),
        )
        prototype.set_threshold(selection.threshold)
        prototype.freeze()
        selections[name] = {
            "threshold": selection.threshold,
            "safe": selection.safe,
            "confidence": selection.confidence,
        }
        tables.append(table)
    calibration = pd.concat(tables, ignore_index=True)
    calibration.to_csv(artifacts / "calibration.csv", index=False)

    test_rows: list[dict] = []
    for name, prototype in prototypes.items():
        print(f"testing {name}", flush=True)
        test_rows.extend(
            _run_tasks(
                config,
                prototype,
                test_ids,
                "balanced_default",
                {},
                seed=0,
                world=0,
                policy_name=name,
            )
        )
    test = pd.DataFrame(test_rows).fillna(0)
    test.to_parquet(artifacts / "test_results.parquet", index=False)
    summary = _policy_summary(test)
    terminal_attempts = test.groupby("policy")["terminal_action_count"].sum()
    summary["terminal_action_count"] = summary["policy"].map(terminal_attempts).fillna(0)
    summary.to_csv(artifacts / "policy_summary.csv", index=False)

    gates = evaluate_diagnostic_gates(calibration, summary, selections)
    authorized = all(bool(item["pass"]) for item in gates.values())
    checklist = {
        "authorized_for_larger_run": authorized,
        "gates": gates,
        "status": "PARTIAL",
    }
    (artifacts / "gate_checklist.json").write_text(json.dumps(checklist, indent=2))
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "UNCOMMITTED"
    elapsed = time.time() - start
    (artifacts / "repair_report.md").write_text(
        _report(commit, elapsed, config, calibration, summary, selections, gates)
    )
    return "PARTIAL"
