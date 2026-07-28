# CCR-VOC computational evaluation

This report evaluates behavior only inside the declared synthetic simulator. It does not establish novelty, optimality, real-world validation, or commercial value.

## Bounded repair-cycle addendum

One bounded repair cycle was executed after the original fast experiment. The repaired source
commit is `227ac67736458734db07d28a3907a8eef986f6f8`. The repair corrected the scheduled-policy
cursor, exposed specification review to policies, removed stale evidence from the particle
posterior after candidate mutation, improved diminishing-return handling, and added controlled
acceptance-capability tests. It did not alter or overwrite the original fast-experiment results.

Verification executed on the repaired commit:

- `UV_CACHE_DIR=/tmp/ccrvoc-repair-uv uv run ruff format --check .` — passed.
- `UV_CACHE_DIR=/tmp/ccrvoc-repair-uv uv run ruff check .` — passed.
- `UV_CACHE_DIR=/tmp/ccrvoc-repair-uv uv run mypy src` — passed for 34 source files.
- `UV_CACHE_DIR=/tmp/ccrvoc-repair-uv uv run pytest -q` — 33 tests passed.
- `UV_CACHE_DIR=/tmp/ccrvoc-repair-uv MPLCONFIGDIR=/tmp/ccrvoc-mpl uv run ccrvoc diagnostic --config configs/diagnostic.yaml --output artifacts/repair_diagnostic` — completed in 254.925 seconds with the configured 2,000 training, 1,500 calibration, and 1,000 disjoint-test tasks.

The diagnostic failed four of five scale-up gates:

- Calibration support: fixed compute 321 accepted, greedy confidence 104, known-model CCR-VOC 0,
  and learned-model CCR-VOC 3; the required minimum was 100 per serious policy.
- No baseline was safe under Bonferroni-adjusted policy-level calibration. At its selected
  threshold, fixed compute had calibration FAR 0.2025 (upper bound 0.2577), while greedy
  confidence had FAR 0.1442 (upper bound 0.2389).
- On the disjoint test, both CCR-VOC modes accepted 0/1,000 tasks and had VUD 0. Their one-sided
  95% false-acceptance upper bounds are therefore 1.0, not evidence of safety.
- Fixed compute achieved test VUD 0.2021 with FAR 0.1498; greedy confidence achieved VUD 0.0940
  with FAR 0.1233. Neither is a safe comparison baseline.
- Budget and terminal-state invariants passed: zero budget violations and zero post-terminal
  action attempts.

The causal logging diagnostic had minimum propensity 0.0833 and zero overlap violations. The
complete repair-cycle tables, frozen thresholds, task-level Parquet output, and gate evidence are
in `artifacts/repair_diagnostic/repair_report.md` and adjacent machine-readable files.

These executed results do not justify another fast or full experiment. They leave the master
hypothesis unsupported and the repository status remains PARTIAL.

## Reproducibility

- Executed source commit: `b9c399acb06db6eeaebc3833e96f8a44c062f963`
- Environment: `{"PyYAML": "6.0.3", "matplotlib": "3.11.1", "numpy": "2.5.1", "pandas": "3.0.5", "python": "3.12.13", "scikit-learn": "1.9.0", "scipy": "1.18.0"}`
- Commands executed:

  - `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv sync --extra dev`
  - `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run pytest`
  - `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run ruff check .`
  - `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run mypy src`
  - `GIT_DIR=.ccrvoc-git GIT_WORK_TREE=. UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run ccrvoc run --config configs/fast.yaml --output artifacts`
  - `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache MPLCONFIGDIR=/tmp/ccrvoc-matplotlib uv run ccrvoc finalize --config configs/fast.yaml --output artifacts --executed-commit b9c399acb06db6eeaebc3833e96f8a44c062f963`

## Resolved configuration

```yaml
ablations:
- posterior_mean
- no_correlation
- no_evidence_invalidation
- h1
- h3
- no_diminishing_returns
- no_causal_adjustment
- uncalibrated_threshold
action_means:
  adversarial_review:
    cost: 0.35
    seconds: 40
  context:
    cost: 0.08
    seconds: 15
  debug:
    cost: 0.25
    seconds: 30
  diverse_alternative:
    cost: 0.55
    seconds: 45
  fuzz_security:
    cost: 0.25
    seconds: 35
  independent_review:
    cost: 0.2
    seconds: 25
  integration_test:
    cost: 0.12
    seconds: 18
  primary_generation:
    cost: 0.35
    seconds: 30
  repair:
    cost: 0.2
    seconds: 25
  reviewer_rerun:
    cost: 0.18
    seconds: 22
  same_family_alternative:
    cost: 0.4
    seconds: 35
  unit_test:
    cost: 0.06
    seconds: 8
adversarial_regimes:
  competence_drift:
    competence_resample_period: 100
  confidence_inversion:
    confidence_inversion: true
  context_poisoning:
    context_effect_sign: 1.0
  hidden_catastrophic_defect:
    catastrophic_probability: 0.001
  hidden_reviewer_correlation:
    model_gamma_cap: 0.5
    true_reviewer_gamma: 0.95
  high_repair_regression:
    regression_max: 0.3
    regression_min: 0.15
  missing_causal_overlap:
    minimum_training_propensity: 0.0
  pareto_cost_duration:
    pareto_shape: 1.5
  shared_specification_trap:
    spec_trap_shift: 2.0
  verifier_degradation:
    post_calibration_sensitivity_multiplier: 0.6
cost_cv: 0.15
duration_cv: 0.25
ensemble_members: 4
epsilon_voc_fraction: 0.01
family_gamma:
  different_model_same_suite: 0.4
  distinct_families: 0.1
  exact_rerun: 0.85
  independent_reviewer_family: 0.2
  same_family_changed_prompt: 0.6
lambda_time: 0.0001
mode: fast
model_modes:
- known_model
- learned_model
particles: 300
planning_depth: 2
regimes:
  balanced_default: {}
  high_modeled_correlation:
    gamma_multiplier: 1.35
  high_task_difficulty:
    difficulty_shift: 0.7
  low_monetary_budgets:
    budget_multiplier: 0.65
  noisy_verifiers:
    false_positive_multiplier: 1.7
    sensitivity_multiplier: 0.7
  tight_deadlines:
    deadline_multiplier: 0.55
rho: 1.0
risk_threshold_grid:
- 0.001
- 0.002
- 0.005
- 0.01
- 0.02
- 0.03
- 0.05
- 0.075
- 0.1
- 0.15
- 0.2
seed: 20260728
sizes:
  adversarial_seeds: 2
  adversarial_tasks_per_seed: 500
  calibration: 5000
  nominal_seeds: 3
  nominal_tasks_per_seed: 500
  training: 10000
  validation: 3000
```

## Test results

Executed before the experiment:

- `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run pytest`
  - `26 passed in 4.94s`
- `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run ruff check .`
  - `All checks passed!`
- `UV_CACHE_DIR=/tmp/ccrvoc-uv-cache uv run mypy src`
  - `Success: no issues found in 33 source files`


## Training and overlap diagnostics

The learned model uses inverse-propensity-weighted logistic transition fitting. Minimum logged propensity was 0.0833; recorded overlap violations: 0.

## Calibration

| policy | threshold | tasks | accepted | incorrect | far | far_upper_bonferroni | vud | safe | split |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ccr_voc_learned | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_learned | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ccr_voc_known | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_compute | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| fixed_retry | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| generate_review | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| greedy_confidence | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| epsilon_bandit | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| thompson | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| ucb1 | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linear_thompson | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.001 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.002 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.005 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.01 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.02 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.03 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.05 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.075 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.1 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.15 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |
| linucb | 0.2 | 5000 | 0 | 0 | 0 | 1 | 0 | False | calibration |

## Nominal policy comparison

| policy | vud | correct_utility_per_task | far | severity_weighted_far | acceptance_coverage | correct_acceptance_rate | failure_declaration_rate | cost_per_task | cost_per_correct_task | deadline_miss_rate | budget_violation_rate | scheduler_overhead_seconds | stale_evidence_invalidations | accepted | false_accepts | tasks | far_upper_95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ccr_voc_known | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.44904 | 22041.3 | 0.131 | 0 | 129.468 | 0 | 0 | 0 | 9000 | 1 |
| ccr_voc_learned | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.55438 | 22989.5 | 0.137 | 0 | 233.91 | 0 | 0 | 0 | 9000 | 1 |
| epsilon_bandit | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.583715 | 5253.43 | 0.00222222 | 0 | 1.17626 | 171 | 0 | 0 | 9000 | 1 |
| fixed_compute | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.04004 | 27360.3 | 0.158889 | 0 | 0.850711 | 0 | 0 | 0 | 9000 | 1 |
| fixed_retry | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.05405 | 27486.5 | 0.155444 | 0 | 0.818786 | 0 | 0 | 0 | 9000 | 1 |
| generate_review | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.05405 | 27486.5 | 0.155444 | 0 | 0.798451 | 0 | 0 | 0 | 9000 | 1 |
| greedy_confidence | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.829824 | 7468.42 | 0.0148889 | 0 | 8.9816 | 0 | 0 | 0 | 9000 | 1 |
| linear_thompson | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.588035 | 5292.32 | 0.00233333 | 0 | 9.08551 | 29 | 0 | 0 | 9000 | 1 |
| linucb | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550778 | 4957 | 0.000111111 | 0 | 2.09871 | 0 | 0 | 0 | 9000 | 1 |
| thompson | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550494 | 4954.45 | 0.000111111 | 0 | 1.35932 | 0 | 0 | 0 | 9000 | 1 |
| ucb1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550257 | 4952.31 | 0 | 0 | 0.775724 | 0 | 0 | 0 | 9000 | 1 |

## Adversarial and nominal regime results

| policy | regime | vud | correct_utility_per_task | far | severity_weighted_far | acceptance_coverage | correct_acceptance_rate | failure_declaration_rate | cost_per_task | cost_per_correct_task | deadline_miss_rate | budget_violation_rate | scheduler_overhead_seconds | stale_evidence_invalidations | accepted | false_accepts | tasks | far_upper_95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ccr_voc_known | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.68711 | 4030.66 | 0.0253333 | 0 | 23.4791 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_known | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.69287 | 2692.87 | 0.009 | 0 | 16.4477 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.50841 | 2508.41 | 0.029 | 0 | 16.2153 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.62171 | 2621.71 | 0.024 | 0 | 15.5054 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.66479 | 2664.79 | 0.02 | 0 | 15.3542 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.70071 | 2700.71 | 0.016 | 0 | 16.053 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.71898 | 4078.47 | 0.0226667 | 0 | 23.5589 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_known | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.72946 | 2729.46 | 0.029 | 0 | 15.9949 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.57537 | 3863.05 | 0.034 | 0 | 24.0049 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_known | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1.8546 | 2781.9 | 0 | 0 | 17.3641 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_known | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.65876 | 2658.76 | 0.026 | 0 | 15.8758 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.6447 | 3967.04 | 0.026 | 0 | 23.2483 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_known | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.03378 | 2033.78 | 0.122 | 0 | 15.023 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.54995 | 2549.95 | 0.028 | 0 | 15.0439 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_known | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.21348 | 3320.21 | 0.678 | 0 | 17.813 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_known | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.74542 | 2745.42 | 0.025 | 0 | 15.9254 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.82194 | 4232.91 | 0.0266667 | 0 | 42.2408 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_learned | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.82718 | 2827.18 | 0.014 | 0 | 29.5617 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.66748 | 2667.48 | 0.028 | 0 | 30.5728 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.7728 | 2772.8 | 0.027 | 0 | 28.1675 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.78939 | 2789.39 | 0.023 | 0 | 28.672 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.83845 | 2838.45 | 0.019 | 0 | 28.73 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.84164 | 4262.46 | 0.024 | 0 | 42.5219 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_learned | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.85358 | 2853.58 | 0.037 | 0 | 28.6497 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.72414 | 4086.21 | 0.0286667 | 0 | 43.3438 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_learned | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1.90697 | 2860.45 | 0 | 0 | 29.4969 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_learned | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.7814 | 2781.4 | 0.028 | 0 | 27.9114 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.79204 | 4188.06 | 0.036 | 0 | 42.4098 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_learned | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.11091 | 2110.91 | 0.131 | 0 | 27.1786 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.69109 | 2691.09 | 0.019 | 0 | 27.7942 | 0 | 0 | 0 | 1000 | 1 |
| ccr_voc_learned | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.23958 | 3359.37 | 0.706667 | 0 | 33.8967 | 0 | 0 | 0 | 1500 | 1 |
| ccr_voc_learned | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.86013 | 2860.13 | 0.017 | 0 | 28.4856 | 0 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.582252 | 873.379 | 0 | 0 | 0.204994 | 31 | 0 | 0 | 1500 | 1 |
| epsilon_bandit | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.586663 | 586.663 | 0 | 0 | 0.128537 | 27 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.585054 | 585.054 | 0.001 | 0 | 0.155195 | 30 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.595637 | 595.637 | 0 | 0 | 0.129 | 26 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.589193 | 589.193 | 0 | 0 | 0.132184 | 24 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.583346 | 583.346 | 0 | 0 | 0.134325 | 16 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.584454 | 876.68 | 0 | 0 | 0.198368 | 30 | 0 | 0 | 1500 | 1 |
| epsilon_bandit | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.580103 | 580.103 | 0 | 0 | 0.125838 | 10 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.582944 | 874.416 | 0 | 0 | 0.192212 | 25 | 0 | 0 | 1500 | 1 |
| epsilon_bandit | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.579916 | 869.874 | 0 | 0 | 0.206199 | 29 | 0 | 0 | 1500 | 1 |
| epsilon_bandit | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.591705 | 591.705 | 0.002 | 0 | 0.133005 | 30 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.588226 | 882.339 | 0 | 0 | 0.191864 | 30 | 0 | 0 | 1500 | 1 |
| epsilon_bandit | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.460474 | 460.474 | 0.01 | 0 | 0.16006 | 11 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.578155 | 578.155 | 0 | 0 | 0.127245 | 13 | 0 | 0 | 1000 | 1 |
| epsilon_bandit | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.584497 | 876.746 | 0.0133333 | 0 | 0.182624 | 26 | 0 | 0 | 1500 | 1 |
| epsilon_bandit | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.582031 | 582.031 | 0 | 0 | 0.127121 | 21 | 0 | 0 | 1000 | 1 |
| fixed_compute | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.36375 | 5045.63 | 0.00266667 | 0 | 0.162914 | 0 | 0 | 0 | 1500 | 1 |
| fixed_compute | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.38295 | 3382.95 | 0.002 | 0 | 0.108203 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.3178 | 3317.8 | 0 | 0 | 0.10701 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.32805 | 3328.05 | 0.001 | 0 | 0.109579 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.32397 | 3323.97 | 0 | 0 | 0.103998 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.41111 | 3411.11 | 0 | 0 | 0.107866 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.39404 | 5091.06 | 0.000666667 | 0 | 0.171093 | 0 | 0 | 0 | 1500 | 1 |
| fixed_compute | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.31525 | 3315.25 | 0.002 | 0 | 0.10942 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.29774 | 4946.61 | 0.000666667 | 0 | 0.158928 | 0 | 0 | 0 | 1500 | 1 |
| fixed_compute | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.10681 | 3160.22 | 0 | 0 | 0.0848103 | 0 | 0 | 0 | 1500 | 1 |
| fixed_compute | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.3213 | 3321.3 | 0 | 0 | 0.112817 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.34428 | 5016.42 | 0.000666667 | 0 | 0.170353 | 0 | 0 | 0 | 1500 | 1 |
| fixed_compute | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.81979 | 2819.79 | 0.224 | 0 | 0.134097 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.29965 | 3299.65 | 0.001 | 0 | 0.106239 | 0 | 0 | 0 | 1000 | 1 |
| fixed_compute | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.73358 | 4100.37 | 0.948667 | 0 | 0.102613 | 0 | 0 | 0 | 1500 | 1 |
| fixed_compute | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.38324 | 3383.24 | 0.001 | 0 | 0.112521 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.36287 | 5044.31 | 0 | 0 | 0.160703 | 0 | 0 | 0 | 1500 | 1 |
| fixed_retry | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.40007 | 3400.07 | 0 | 0 | 0.108332 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.31937 | 3319.37 | 0.001 | 0 | 0.104519 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.33447 | 3334.47 | 0 | 0 | 0.111684 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.33094 | 3330.94 | 0 | 0 | 0.10297 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.42506 | 3425.06 | 0 | 0 | 0.115531 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.39034 | 5085.51 | 0 | 0 | 0.163788 | 0 | 0 | 0 | 1500 | 1 |
| fixed_retry | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.32224 | 3322.24 | 0 | 0 | 0.110325 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.30534 | 4958 | 0 | 0 | 0.157855 | 0 | 0 | 0 | 1500 | 1 |
| fixed_retry | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.10023 | 3150.34 | 0 | 0 | 0.0821695 | 0 | 0 | 0 | 1500 | 1 |
| fixed_retry | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.33674 | 3336.74 | 0 | 0 | 0.122505 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.35246 | 5028.68 | 0 | 0 | 0.153872 | 0 | 0 | 0 | 1500 | 1 |
| fixed_retry | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.82807 | 2828.07 | 0.201 | 0 | 0.133812 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.30149 | 3301.49 | 0 | 0 | 0.104474 | 0 | 0 | 0 | 1000 | 1 |
| fixed_retry | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.81307 | 4219.6 | 0.932667 | 0 | 0.100398 | 0 | 0 | 0 | 1500 | 1 |
| fixed_retry | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.38477 | 3384.77 | 0 | 0 | 0.106465 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.36287 | 5044.31 | 0 | 0 | 0.15735 | 0 | 0 | 0 | 1500 | 1 |
| generate_review | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.40007 | 3400.07 | 0 | 0 | 0.111096 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.31937 | 3319.37 | 0.001 | 0 | 0.100221 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.33447 | 3334.47 | 0 | 0 | 0.102502 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.33094 | 3330.94 | 0 | 0 | 0.104445 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.42506 | 3425.06 | 0 | 0 | 0.11311 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.39034 | 5085.51 | 0 | 0 | 0.159746 | 0 | 0 | 0 | 1500 | 1 |
| generate_review | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.32224 | 3322.24 | 0 | 0 | 0.103272 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.30534 | 4958 | 0 | 0 | 0.152201 | 0 | 0 | 0 | 1500 | 1 |
| generate_review | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.10023 | 3150.34 | 0 | 0 | 0.0795547 | 0 | 0 | 0 | 1500 | 1 |
| generate_review | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.33674 | 3336.74 | 0 | 0 | 0.106507 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.35246 | 5028.68 | 0 | 0 | 0.15146 | 0 | 0 | 0 | 1500 | 1 |
| generate_review | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.82807 | 2828.07 | 0.201 | 0 | 0.128917 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.30149 | 3301.49 | 0 | 0 | 0.10512 | 0 | 0 | 0 | 1000 | 1 |
| generate_review | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2.81307 | 4219.6 | 0.932667 | 0 | 0.0981388 | 0 | 0 | 0 | 1500 | 1 |
| generate_review | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3.38477 | 3384.77 | 0 | 0 | 0.105039 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.827721 | 1241.58 | 0 | 0 | 1.54655 | 0 | 0 | 0 | 1500 | 1 |
| greedy_confidence | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.83275 | 832.75 | 0 | 0 | 0.994897 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.82887 | 828.87 | 0 | 0 | 1.02727 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.8326 | 832.6 | 0 | 0 | 1.02134 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.82682 | 826.82 | 0 | 0 | 0.985738 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.830258 | 830.258 | 0 | 0 | 1.0027 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.830741 | 1246.11 | 0 | 0 | 1.47887 | 0 | 0 | 0 | 1500 | 1 |
| greedy_confidence | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.828376 | 828.376 | 0 | 0 | 0.991419 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.831314 | 1246.97 | 0 | 0 | 1.48356 | 0 | 0 | 0 | 1500 | 1 |
| greedy_confidence | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.828255 | 1242.38 | 0 | 0 | 1.46178 | 0 | 0 | 0 | 1500 | 1 |
| greedy_confidence | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.830404 | 830.404 | 0 | 0 | 1.00551 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.83216 | 1248.24 | 0 | 0 | 1.51011 | 0 | 0 | 0 | 1500 | 1 |
| greedy_confidence | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.687853 | 687.853 | 0.021 | 0 | 0.955931 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.826848 | 826.848 | 0 | 0 | 0.992356 | 0 | 0 | 0 | 1000 | 1 |
| greedy_confidence | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.828754 | 1243.13 | 0.0893333 | 0 | 1.50072 | 0 | 0 | 0 | 1500 | 1 |
| greedy_confidence | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.826954 | 826.954 | 0 | 0 | 1.07134 | 0 | 0 | 0 | 1000 | 1 |
| linear_thompson | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.562027 | 843.04 | 0 | 0 | 1.50982 | 3 | 0 | 0 | 1500 | 1 |
| linear_thompson | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.569876 | 569.876 | 0.001 | 0 | 0.987291 | 7 | 0 | 0 | 1000 | 1 |
| linear_thompson | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.563158 | 563.158 | 0 | 0 | 1.00763 | 0 | 0 | 0 | 1000 | 1 |
| linear_thompson | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.571809 | 571.809 | 0 | 0 | 0.973604 | 3 | 0 | 0 | 1000 | 1 |
| linear_thompson | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.559009 | 559.009 | 0 | 0 | 1.11289 | 4 | 0 | 0 | 1000 | 1 |
| linear_thompson | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.560875 | 560.875 | 0 | 0 | 0.999141 | 0 | 0 | 0 | 1000 | 1 |
| linear_thompson | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.562176 | 843.264 | 0 | 0 | 1.4968 | 0 | 0 | 0 | 1500 | 1 |
| linear_thompson | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.561227 | 561.227 | 0 | 0 | 0.996643 | 3 | 0 | 0 | 1000 | 1 |
| linear_thompson | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.567125 | 850.688 | 0 | 0 | 1.48429 | 0 | 0 | 0 | 1500 | 1 |
| linear_thompson | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.629097 | 943.645 | 0 | 0 | 1.56467 | 13 | 0 | 0 | 1500 | 1 |
| linear_thompson | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.563955 | 563.955 | 0 | 0 | 1.05364 | 4 | 0 | 0 | 1000 | 1 |
| linear_thompson | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.565848 | 848.773 | 0 | 0 | 1.46535 | 1 | 0 | 0 | 1500 | 1 |
| linear_thompson | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.451034 | 451.034 | 0.008 | 0 | 0.981806 | 0 | 0 | 0 | 1000 | 1 |
| linear_thompson | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.565767 | 565.767 | 0 | 0 | 0.974796 | 3 | 0 | 0 | 1000 | 1 |
| linear_thompson | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.641938 | 962.908 | 0.014 | 0 | 1.56459 | 12 | 0 | 0 | 1500 | 1 |
| linear_thompson | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.55831 | 558.31 | 0 | 0 | 1.0725 | 6 | 0 | 0 | 1000 | 1 |
| linucb | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548557 | 822.836 | 0 | 0 | 0.348355 | 0 | 0 | 0 | 1500 | 1 |
| linucb | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.555591 | 555.591 | 0 | 0 | 0.22354 | 0 | 0 | 0 | 1000 | 1 |
| linucb | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550731 | 550.731 | 0 | 0 | 0.224086 | 0 | 0 | 0 | 1000 | 1 |
| linucb | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.555948 | 555.948 | 0 | 0 | 0.244352 | 0 | 0 | 0 | 1000 | 1 |
| linucb | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.546786 | 546.786 | 0 | 0 | 0.228919 | 0 | 0 | 0 | 1000 | 1 |
| linucb | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550843 | 550.843 | 0 | 0 | 0.2321 | 0 | 0 | 0 | 1000 | 1 |
| linucb | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550707 | 826.06 | 0 | 0 | 0.356807 | 0 | 0 | 0 | 1500 | 1 |
| linucb | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548743 | 548.743 | 0 | 0 | 0.222671 | 0 | 0 | 0 | 1000 | 1 |
| linucb | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.552956 | 829.434 | 0 | 0 | 0.357284 | 0 | 0 | 0 | 1500 | 1 |
| linucb | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550376 | 825.564 | 0 | 0 | 0.340718 | 0 | 0 | 0 | 1500 | 1 |
| linucb | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550514 | 550.514 | 0 | 0 | 0.225637 | 0 | 0 | 0 | 1000 | 1 |
| linucb | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.551283 | 826.924 | 0 | 0 | 0.349306 | 0 | 0 | 0 | 1500 | 1 |
| linucb | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.438284 | 438.284 | 0.008 | 0 | 0.222492 | 0 | 0 | 0 | 1000 | 1 |
| linucb | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.549796 | 549.796 | 0 | 0 | 0.233584 | 0 | 0 | 0 | 1000 | 1 |
| linucb | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550791 | 826.186 | 0.000666667 | 0 | 0.34624 | 0 | 0 | 0 | 1500 | 1 |
| linucb | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548635 | 548.635 | 0 | 0 | 0.23426 | 0 | 0 | 0 | 1000 | 1 |
| thompson | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548481 | 822.721 | 0 | 0 | 0.220568 | 0 | 0 | 0 | 1500 | 1 |
| thompson | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.555166 | 555.166 | 0 | 0 | 0.140602 | 0 | 0 | 0 | 1000 | 1 |
| thompson | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550031 | 550.031 | 0 | 0 | 0.199527 | 0 | 0 | 0 | 1000 | 1 |
| thompson | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.555422 | 555.422 | 0 | 0 | 0.138399 | 0 | 0 | 0 | 1000 | 1 |
| thompson | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.546218 | 546.218 | 0 | 0 | 0.156263 | 0 | 0 | 0 | 1000 | 1 |
| thompson | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550189 | 550.189 | 0 | 0 | 0.154016 | 0 | 0 | 0 | 1000 | 1 |
| thompson | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550233 | 825.349 | 0 | 0 | 0.23299 | 0 | 0 | 0 | 1500 | 1 |
| thompson | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548218 | 548.218 | 0 | 0 | 0.150281 | 0 | 0 | 0 | 1000 | 1 |
| thompson | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.552394 | 828.591 | 0 | 0 | 0.221604 | 0 | 0 | 0 | 1500 | 1 |
| thompson | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550187 | 825.281 | 0 | 0 | 0.240081 | 0 | 0 | 0 | 1500 | 1 |
| thompson | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550037 | 550.037 | 0 | 0 | 0.159806 | 0 | 0 | 0 | 1000 | 1 |
| thompson | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550721 | 826.082 | 0 | 0 | 0.224932 | 0 | 0 | 0 | 1500 | 1 |
| thompson | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.437205 | 437.205 | 0.008 | 0 | 0.161115 | 0 | 0 | 0 | 1000 | 1 |
| thompson | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.54954 | 549.54 | 0 | 0 | 0.150284 | 0 | 0 | 0 | 1000 | 1 |
| thompson | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.55095 | 826.425 | 0.000666667 | 0 | 0.219147 | 0 | 0 | 0 | 1500 | 1 |
| thompson | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.547012 | 547.012 | 0 | 0 | 0.143934 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | balanced_default | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548011 | 822.017 | 0 | 0 | 0.132061 | 0 | 0 | 0 | 1500 | 1 |
| ucb1 | competence_drift | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.55483 | 554.83 | 0 | 0 | 0.0877357 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | confidence_inversion | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.549803 | 549.803 | 0 | 0 | 0.0812657 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | context_poisoning | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.555249 | 555.249 | 0 | 0 | 0.0848692 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | hidden_catastrophic_defect | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.545897 | 545.897 | 0 | 0 | 0.0893625 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | hidden_reviewer_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.549486 | 549.486 | 0 | 0 | 0.0905785 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | high_modeled_correlation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550164 | 825.246 | 0 | 0 | 0.134665 | 0 | 0 | 0 | 1500 | 1 |
| ucb1 | high_repair_regression | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548115 | 548.115 | 0 | 0 | 0.089723 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | high_task_difficulty | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.552242 | 828.362 | 0 | 0 | 0.131906 | 0 | 0 | 0 | 1500 | 1 |
| ucb1 | low_monetary_budgets | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.54999 | 824.985 | 0 | 0 | 0.131243 | 0 | 0 | 0 | 1500 | 1 |
| ucb1 | missing_causal_overlap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.549672 | 549.672 | 0 | 0 | 0.0861099 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | noisy_verifiers | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550638 | 825.956 | 0 | 0 | 0.122797 | 0 | 0 | 0 | 1500 | 1 |
| ucb1 | pareto_cost_duration | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.436653 | 436.653 | 0.008 | 0 | 0.0816005 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | shared_specification_trap | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.548836 | 548.836 | 0 | 0 | 0.0862154 | 0 | 0 | 0 | 1000 | 1 |
| ucb1 | tight_deadlines | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.550496 | 825.744 | 0 | 0 | 0.123052 | 0 | 0 | 0 | 1500 | 1 |
| ucb1 | verifier_degradation | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.546925 | 546.925 | 0 | 0 | 0.0914343 | 0 | 0 | 0 | 1000 | 1 |

The adversarial regimes are diagnostic attacks and are not required to pass. Their failures quantify where calibration or model assumptions break.

## Ablations

See `ablation_summary.csv`. Ablations are diagnostic and do not select the main threshold.

## Acceptance criteria

| Criterion | Pass | Evidence |
|---|---:|---|
| 1 pooled FAR upper bound <= 0.05 | False | upper=1.000000 |
| 2 weighted FAR upper bound <= 0.05 | False | point=0.000000, bootstrap_upper=1.000000 |
| 3 absolute FAR increase upper <= 0.005 | False | no baseline met final-test safety bound |
| 5 VUD point improvement >= 10% | False | no baseline met final-test safety bound |
| 6 paired-bootstrap relative VUD lower > 3% | False | no baseline met final-test safety bound |
| 7 correct utility not >2% below baseline | False | no baseline met final-test safety bound |
| 4 no regime FAR upper bound > 0.10 | False | maximum=1.000000 |
| 8 pooled and at least four regimes | False | regimes=0/6 |
| 9 budget violation exactly zero | True | violations=0 |
| 10 no actions after terminal | True | attempts=0 |
| 11 scheduler overhead <=10% cost | True | assumption=$0.0001/s, fraction=0.000001 |

## Limitations and simulator-dependent assumptions

- Fast mode is a code-validation experiment and is explicitly barred from producing PASS.
- The configured Gaussian-copula gamma is latent-normal correlation, not generally the Pearson correlation of thresholded binary flags.
- Simulated agents, reviewers, repairs, prices, and deadlines are assumptions rather than measurements of deployed systems.
- The particle rollouts approximate the declared transition family; finite ensemble and Monte Carlo error remain.
- Adversarial distribution shifts can invalidate calibration, especially verifier degradation and hidden correlation.

## Final status

PARTIAL
