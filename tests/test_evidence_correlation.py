import numpy as np

from ccrvoc.evidence import binary_gaussian_copula_corr, simulate_correlation


def test_latent_and_binary_copula_correlations_emerge() -> None:
    gamma = 0.60
    probe = simulate_correlation(gamma, 150_000, 123)
    latent = np.corrcoef(probe.latent_a, probe.latent_b)[0, 1]
    observed = np.corrcoef(probe.flags_a, probe.flags_b)[0, 1]
    assert abs(latent - gamma) < 0.015
    assert abs(observed - binary_gaussian_copula_corr(gamma)) < 0.015
    assert abs(observed - gamma) > 0.05  # thresholding does not preserve Pearson gamma
