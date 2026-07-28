from __future__ import annotations

import numpy as np
from scipy.stats import beta


def clopper_pearson_upper(errors: int, trials: int, confidence: float = 0.95) -> float:
    if trials == 0:
        return 1.0
    if errors == trials:
        return 1.0
    return float(beta.ppf(confidence, errors + 1, trials - errors))


def paired_bootstrap_relative_vud(
    work_a: np.ndarray,
    cost_a: np.ndarray,
    work_b: np.ndarray,
    cost_b: np.ndarray,
    rng: np.random.Generator,
    n_boot: int = 2000,
) -> tuple[float, float, float]:
    n = len(work_a)
    estimates = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        va = work_a[idx].sum() / max(cost_a[idx].sum(), 1e-12)
        vb = work_b[idx].sum() / max(cost_b[idx].sum(), 1e-12)
        estimates[b] = va / max(vb, 1e-12) - 1
    point = work_a.sum() / max(cost_a.sum(), 1e-12)
    reference = work_b.sum() / max(cost_b.sum(), 1e-12)
    return (
        float(point / max(reference, 1e-12) - 1),
        float(np.quantile(estimates, 0.025)),
        float(np.quantile(estimates, 0.975)),
    )
