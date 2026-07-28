# Methodology

## Evaluation principle

Policies must act without access to hidden oracle correctness. The simulator
uses the oracle only to score accepted outputs after policy decisions are
complete. This separates policy-visible evidence from evaluation truth.

## Task and action model

Tasks vary in difficulty, value, monetary budget, deadline, and latent defect
state. Policies may request generation, context, review, tests, debugging,
repair, reruns, or alternative candidates. Actions have stochastic monetary
cost and duration. An action that crosses the deadline consumes its sampled
cost and time but produces no usable output.

## Correlated evidence

Agent and verifier failures are correlated through evidence families. The
configured `gamma` is a latent-normal correlation in a Gaussian-copula model,
not generally the Pearson correlation of thresholded binary outcomes. Tests
check both the latent and analytically implied binary correlations.

Evidence tied to an earlier candidate becomes stale after candidate mutation
and is invalidated. This prevents a repaired or replaced candidate from
retaining unsupported confidence.

## Learned transition model

The learned CCR-VOC mode fits inverse-propensity-weighted logistic transition
models from a separate training split. Logged action propensities support
overlap diagnostics. The bounded diagnostic recorded a minimum propensity of
0.0833 and zero overlap violations.

## Calibration and testing

Training, calibration, and final testing use disjoint generated tasks. Risk
thresholds are selected on calibration data and frozen before the final test.
The diagnostic applies policy-level Bonferroni adjustment when computing
false-acceptance upper bounds.

Zero accepted tasks do not establish safety. The implementation assigns a
false-acceptance upper bound of 1.0 when a policy has no accepted observations.

## Metrics

Primary metrics include:

- verified useful work per dollar (VUD);
- acceptance coverage;
- correct utility per task;
- false-acceptance rate (FAR);
- severity-weighted FAR;
- one-sided FAR confidence bounds;
- deadline-miss and budget-violation rates;
- scheduler overhead;
- stale-evidence invalidations.

## Adversarial regimes

The broader harness includes competence drift, confidence inversion, context
poisoning, hidden catastrophic defects, hidden reviewer correlation, elevated
repair regression, missing causal overlap, heavy-tailed cost/duration,
shared-specification traps, and verifier degradation.

## Gate logic

The bounded diagnostic blocks scale-up if any of these fail:

1. sufficient accepted calibration examples for every serious policy;
2. at least one statistically safe baseline;
3. positive CCR-VOC VUD;
4. calibrated risk bounds;
5. exact budget and terminal-state invariants.

The executed diagnostic passed only item 5. The larger experiment was therefore
not authorized.

## Reproducibility boundaries

The repository includes the resolved configurations, task-level Parquet
outputs, summary tables, plots, gate checklists, and reports produced by the
completed runs. Results apply only to the declared synthetic model and executed
configurations.

Publication review also found and corrected hash-order dependence in
agent-family shock assignment. Family order is now explicit and tested across
Python hash seeds. Scheduler wall-clock measurements remain naturally
machine-dependent and should not be expected to match byte-for-byte.
