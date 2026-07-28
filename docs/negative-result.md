# Negative experimental result

## Original hypothesis

CCR-VOC was proposed as a correlation-calibrated, risk-constrained
value-of-computation scheduler. The tested hypothesis predicted at least 10%
more verified useful work per dollar than the strongest safe baseline, subject
to false-acceptance, budget, deadline, and terminal-state constraints.

The hypothesis was deliberately falsifiable. A productive policy that violated
the false-acceptance bound would not count as a success, and an apparently safe
policy with no acceptance coverage would not count as useful.

## What was executed

The original experiment implemented a heterogeneous sequential-decision
simulator, CCR-VOC in known- and learned-model modes, fixed and heuristic
baselines, contextual bandits, correlated failures, hidden oracle correctness,
stochastic costs and deadlines, diminishing returns, repairs, regressions,
disjoint calibration, and adversarial regimes.

The original fast experiment ended `PARTIAL`. A single bounded repair cycle
then corrected:

- a scheduled-policy cursor defect;
- missing specification-review visibility;
- stale particle-posterior evidence after candidate mutation;
- overvaluation of alternative generation;
- incomplete diminishing-return handling.

Controlled tests established that independent clean evidence could cross the
acceptance threshold and that warning evidence could block acceptance. The
repaired scheduler was then evaluated end to end using 2,000 training tasks,
1,500 calibration tasks, and 1,000 disjoint-test tasks.

## Observed abstention collapse

Known-model CCR-VOC accepted no calibration tasks at any tested threshold.
Learned-model CCR-VOC accepted only 3 of 1,500 calibration tasks at its selected
threshold, and one was incorrect. Its Bonferroni-adjusted false-acceptance upper
bound was 0.934, far above the 0.05 requirement.

On the disjoint test, both CCR-VOC modes accepted 0 of 1,000 tasks and produced
zero verified useful work per dollar. With no accepted trials, the
false-acceptance upper bound is 1.0; abstention cannot be interpreted as
statistically demonstrated safety.

## Why calibration was unusable

Selective-risk calibration needs enough accepted examples to estimate the
error rate among accepted tasks. The diagnostic required at least 100 selected
calibration acceptances per serious policy. Known CCR-VOC produced 0 and learned
CCR-VOC produced 3. This is a coverage failure, not a merely imprecise estimate
that can be repaired by reporting a more favorable point statistic.

## Why larger sample sizes were not justified

The decisive failures occurred before statistical scale became the limiting
issue:

1. The planner rarely found positive expected value for continued computation.
2. The resulting policy almost never reached acceptance.
3. Near-zero acceptance prevented useful risk calibration.
4. The disjoint test confirmed zero useful-work coverage.

A larger run of the same mechanism would spend substantially more compute
without addressing the planning horizon, value estimation, or coverage
failure. Redesign should precede scale-up.

## Productive but unsafe baselines

Fixed compute accepted 207 of 1,000 test tasks and achieved VUD 0.2021, but its
false-acceptance rate was 14.98%. Greedy confidence accepted 73 tasks and
achieved VUD 0.0940, but its false-acceptance rate was 12.33%. These policies
demonstrate that the synthetic environment permits useful work, but neither met
the 5% safety constraint.

No baseline passed the calibrated safety gate, so the candidate's promised
improvement over the strongest safe baseline could not be established.

## What remains unknown

The experiment does not determine:

- whether a different planning horizon or value estimator would work;
- whether another calibration method could maintain both coverage and safety;
- whether the action and observation space admits any safe productive policy;
- whether results transfer outside the synthetic simulator;
- whether a redesigned policy could outperform a safe baseline.

It therefore does not prove that CCR-VOC is impossible or that all
value-of-computation schedulers fail.

## Most valuable next bounded experiment

> Does any policy using the available actions, observations, budgets, and
> deadlines achieve positive useful-work coverage with a statistically
> supported false-acceptance rate of at most 5%?

This is proposed future work, not a completed result. A policy-agnostic
feasibility test would determine whether the current environment and verifier
signal support the desired safety-productivity combination before another
candidate scheduler is designed.

## Evidence

The complete diagnostic is recorded in:

- [`artifacts/repair_diagnostic/repair_report.md`](../artifacts/repair_diagnostic/repair_report.md)
- [`artifacts/repair_diagnostic/gate_checklist.json`](../artifacts/repair_diagnostic/gate_checklist.json)
- [`artifacts/repair_diagnostic/calibration.csv`](../artifacts/repair_diagnostic/calibration.csv)
- [`artifacts/repair_diagnostic/policy_summary.csv`](../artifacts/repair_diagnostic/policy_summary.csv)
- [`artifacts/repair_diagnostic/test_results.parquet`](../artifacts/repair_diagnostic/test_results.parquet)

The bounded repair diagnostic was executed at source commit
`227ac67736458734db07d28a3907a8eef986f6f8`. The earlier fast experiment report
records its executed source commit and environment separately.

## Publication reproducibility correction

The publication review discovered that agent-family shocks were generated by
iterating a Python `set`. Cross-process hash randomization could therefore swap
the deterministic random draws assigned to `F01` and `F2`, changing exact
metrics even though the seed and configuration were unchanged. The frozen
diagnostic happened to use the first-seen family order `F01`, then `F2`.

The public source replaces that unordered iteration with a stable first-seen
order and includes a subprocess regression test using multiple
`PYTHONHASHSEED` values. A clean rerun after this correction reproduced the
frozen calibration, gate checklist, and non-timing policy metrics. The
scientific conclusion and all gate outcomes remain unchanged.
