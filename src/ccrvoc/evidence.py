from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr
from scipy.stats import norm

SENSITIVITY = {
    "unit_test": np.array([0.05, 0.75, 0.35, 0.05, 0.10]),
    "integration_test": np.array([0.10, 0.35, 0.80, 0.10, 0.20]),
    "fuzz_security": np.array([0.05, 0.25, 0.30, 0.80, 0.15]),
    "independent_review": np.array([0.45, 0.60, 0.55, 0.35, 0.35]),
    "adversarial_review": np.array([0.35, 0.55, 0.50, 0.75, 0.55]),
    "spec_review": np.array([0.70, 0.15, 0.10, 0.05, 0.05]),
}
FALSE_POSITIVE = {
    "unit_test": 0.02,
    "integration_test": 0.03,
    "fuzz_security": 0.04,
    "independent_review": 0.08,
    "adversarial_review": 0.12,
    "spec_review": 0.08,
}
FAMILY = {
    "unit_test": "test_unit",
    "integration_test": "test_integration",
    "fuzz_security": "test_security",
    "independent_review": "review_independent",
    "adversarial_review": "review_adversarial",
    "spec_review": "review_spec",
}


def copula_flags(
    base_probability: np.ndarray,
    gamma: float,
    shared_z: np.ndarray,
    epsilon: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    gamma = float(np.clip(gamma, 0, 0.999999))
    latent = np.sqrt(gamma) * shared_z + np.sqrt(1 - gamma) * epsilon
    return ndtr(latent) < base_probability, latent


def binary_gaussian_copula_corr(gamma: float, probability: float = 0.5) -> float:
    if probability == 0.5:
        return float(2 * np.arcsin(gamma) / np.pi)
    threshold = norm.ppf(probability)
    from scipy.stats import multivariate_normal

    joint = multivariate_normal.cdf(
        [threshold, threshold], mean=[0, 0], cov=[[1, gamma], [gamma, 1]]
    )
    return float((joint - probability**2) / (probability * (1 - probability)))


@dataclass
class CorrelationProbe:
    flags_a: np.ndarray
    flags_b: np.ndarray
    latent_a: np.ndarray
    latent_b: np.ndarray


def simulate_correlation(
    gamma: float, n: int, seed: int, probability: float = 0.5
) -> CorrelationProbe:
    rng = np.random.default_rng(seed)
    z = rng.normal(size=n)
    ea = rng.normal(size=n)
    eb = rng.normal(size=n)
    a, la = copula_flags(np.full(n, probability), gamma, z, ea)
    b, lb = copula_flags(np.full(n, probability), gamma, z, eb)
    return CorrelationProbe(a, b, la, lb)
