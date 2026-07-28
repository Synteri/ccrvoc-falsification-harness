# CCR-VOC simulation and falsification harness

This repository implements a heterogeneous sequential-decision simulator for
testing CCR-VOC against calibrated fixed, heuristic, and bandit baselines.
Correctness is a hidden environment oracle: policies receive only task
metadata, candidate identifiers, action outcomes, and non-stale evidence.

The simulator is evidence about behavior *inside the declared synthetic model*.
It does not establish novelty, real-world optimality, experimental validation,
or commercial value.

## Reproduce

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy src
uv run ccrvoc run --config configs/fast.yaml --output artifacts
```

`configs/fast.yaml` preserves the specified fast sample counts and cannot yield
`PASS`. `configs/full.yaml` preserves the specified full counts. A run records
the resolved configuration and refuses to overwrite frozen calibration/model
state during final testing.

## Important statistical interpretation

The evidence mechanism follows the specified Gaussian-copula construction.
The configured `gamma` is a *latent normal correlation*. Except at special
thresholds, Pearson correlation of the thresholded binary flags is not equal to
`gamma`; tests check both the latent correlation and the analytically implied
binary correlation. Treating `gamma` as binary Pearson correlation would be a
modeling error.

Action cost is sampled before the feasibility check inside the environment but
is not shown to the policy. Duration is unknown until completion. An action
whose sampled duration crosses the deadline consumes time and cost and yields
no usable output.

