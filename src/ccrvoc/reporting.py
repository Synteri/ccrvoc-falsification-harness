from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


def _save_plot(path: Path, title: str, x: Any, y: Any, xlabel: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(x, y, marker="o")
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def create_plots(
    artifacts: Path,
    calibration: pd.DataFrame,
    nominal: pd.DataFrame,
    policy_summary: pd.DataFrame,
    regime_summary: pd.DataFrame,
) -> None:
    plots = artifacts / "plots"
    plots.mkdir(exist_ok=True)
    _save_plot(
        plots / "vud_vs_false_acceptance.png",
        "VUD versus selective false acceptance",
        policy_summary["far"],
        policy_summary["vud"],
        "False acceptance",
        "VUD",
    )
    ordered = calibration.sort_values("threshold")
    _save_plot(
        plots / "risk_coverage_frontier.png",
        "Calibration risk–coverage frontier",
        ordered["accepted"] / ordered["tasks"],
        ordered["far"],
        "Coverage",
        "Observed FAR",
    )
    by_class = nominal.groupby(["policy", "task_class"], as_index=False).agg(
        work=("work", "sum"), cost=("cost", "sum")
    )
    by_class["vud"] = by_class["work"] / by_class["cost"].clip(lower=1e-12)
    fig, ax = plt.subplots(figsize=(9, 5))
    for policy, group in by_class.groupby("policy"):
        ax.plot(group["task_class"], group["vud"], marker="o", label=policy)
    ax.set(title="VUD by task class", ylabel="VUD")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(plots / "vud_by_task_class.png", dpi=140)
    plt.close(fig)
    pivot = regime_summary.pivot(index="regime", columns="policy", values="far").fillna(0)
    pivot.plot(kind="bar", figsize=(11, 5), title="False acceptance by regime")
    plt.tight_layout()
    plt.savefig(plots / "false_acceptance_by_regime.png", dpi=140)
    plt.close()
    action_cols = [
        c for c in nominal if c.startswith("action_") and pd.api.types.is_numeric_dtype(nominal[c])
    ]
    allocation = nominal.groupby("policy")[action_cols].sum() if action_cols else pd.DataFrame()
    if not allocation.empty:
        allocation.plot(kind="bar", stacked=True, figsize=(11, 5), title="Action allocation")
        plt.tight_layout()
        plt.savefig(plots / "action_allocation_by_policy.png", dpi=140)
        plt.close()
    repetitions = np.arange(1, 8)
    _save_plot(
        plots / "marginal_return_by_repetition.png",
        "Configured diminishing marginal return",
        repetitions,
        np.exp(-0.7 * (repetitions - 1)),
        "Repetition",
        "Relative information probability",
    )
    _save_plot(
        plots / "calibration_score_vs_error.png",
        "Calibration threshold versus observed error",
        ordered["threshold"],
        ordered["far"],
        "Risk threshold",
        "Observed FAR",
    )
    gammas = np.linspace(0, 0.95, 20)
    implied = 2 * np.arcsin(gammas) / np.pi
    _save_plot(
        plots / "effect_of_evidence_correlation.png",
        "Latent versus binary evidence correlation at p=0.5",
        gammas,
        implied,
        "Latent gamma",
        "Binary Pearson correlation",
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(nominal["cost"], bins=40)
    ax.set(title="Task cost distribution", xlabel="Cost", ylabel="Count")
    fig.tight_layout()
    fig.savefig(plots / "cost_distribution.png", dpi=140)
    plt.close(fig)
    overhead = policy_summary["scheduler_overhead_seconds"]
    _save_plot(
        plots / "scheduler_overhead.png",
        "Scheduler overhead",
        policy_summary["policy"],
        overhead,
        "Policy",
        "Seconds",
    )


def dependency_versions() -> dict[str, str]:
    import matplotlib
    import numpy
    import pandas
    import scipy
    import sklearn
    import yaml as yaml_module

    return {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "pandas": pandas.__version__,
        "scikit-learn": sklearn.__version__,
        "matplotlib": matplotlib.__version__,
        "PyYAML": yaml_module.__version__,
    }


def markdown_table(frame: pd.DataFrame) -> str:
    def cell(value: object) -> str:
        if isinstance(value, float):
            rendered = f"{value:.6g}"
        else:
            rendered = str(value)
        return rendered.replace("|", r"\|").replace("\n", " ")

    columns = [cell(column) for column in frame.columns]
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    rows.extend(
        "| " + " | ".join(cell(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def write_report(
    artifacts: Path,
    config: dict,
    commit_hash: str,
    commands: list[str],
    test_summary: str,
    policy_summary: pd.DataFrame,
    regime_summary: pd.DataFrame,
    calibration: pd.DataFrame,
    overlap: dict,
    acceptance: dict,
    status: str,
) -> None:
    versions = dependency_versions()
    lines = [
        "# CCR-VOC computational evaluation",
        "",
        "This report evaluates behavior only inside the declared synthetic simulator. "
        "It does not establish novelty, optimality, real-world validation, or commercial value.",
        "",
        "## Reproducibility",
        "",
        f"- Executed source commit: `{commit_hash}`",
        f"- Environment: `{json.dumps(versions, sort_keys=True)}`",
        "- Commands executed:",
        "",
        *[f"  - `{command}`" for command in commands],
        "",
        "## Resolved configuration",
        "",
        "```yaml",
        yaml.safe_dump(config, sort_keys=True).rstrip(),
        "```",
        "",
        "## Test results",
        "",
        test_summary,
        "",
        "## Training and overlap diagnostics",
        "",
        "The learned model uses inverse-propensity-weighted logistic transition fitting. "
        f"Minimum logged propensity was {overlap.get('minimum_propensity', 0):.4f}; "
        f"recorded overlap violations: {overlap.get('violations', 0)}.",
        "",
        "## Calibration",
        "",
        markdown_table(calibration),
        "",
        "## Nominal policy comparison",
        "",
        markdown_table(policy_summary),
        "",
        "## Adversarial and nominal regime results",
        "",
        markdown_table(regime_summary),
        "",
        "The adversarial regimes are diagnostic attacks and are not required to pass. "
        "Their failures quantify where calibration or model assumptions break.",
        "",
        "## Ablations",
        "",
        "See `ablation_summary.csv`. Ablations are diagnostic and do not select "
        "the main threshold.",
        "",
        "## Acceptance criteria",
        "",
        "| Criterion | Pass | Evidence |",
        "|---|---:|---|",
    ]
    for name, item in acceptance["criteria"].items():
        lines.append(f"| {name} | {item['pass']} | {item['evidence']} |")
    lines += [
        "",
        "## Limitations and simulator-dependent assumptions",
        "",
        "- Fast mode is a code-validation experiment and is explicitly barred from producing PASS.",
        "- The configured Gaussian-copula gamma is latent-normal correlation, not generally the "
        "Pearson correlation of thresholded binary flags.",
        "- Simulated agents, reviewers, repairs, prices, and deadlines are assumptions rather than "
        "measurements of deployed systems.",
        "- The particle rollouts approximate the declared transition family; finite ensemble and "
        "Monte Carlo error remain.",
        "- Adversarial distribution shifts can invalidate calibration, especially verifier "
        "degradation and hidden correlation.",
        "",
        "## Final status",
        "",
        status,
    ]
    (artifacts / "final_report.md").write_text("\n".join(lines) + "\n")
