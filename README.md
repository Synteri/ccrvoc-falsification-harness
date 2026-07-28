# CCR-VOC: A Falsification Harness for Cost-Aware AI-Agent Scheduling

> **CURRENT RESULT: HYPOTHESIS NOT SUPPORTED**

CCR-VOC is a reproducible synthetic simulator and falsification harness for
resource-bounded AI-agent scheduling under correlated failures, noisy
verification, action costs, deadlines, repairs, regressions, and
false-acceptance constraints. The current CCR-VOC implementation failed to
produce verified useful work in the executed disjoint-test configuration. The
repository is published as an honest negative result and as infrastructure for
testing better scheduling policies.

## Research question

Can a correlation-calibrated, risk-constrained value-of-computation scheduler
produce at least 10% more verified useful work per dollar than the strongest
safe baseline while keeping false acceptance within the specified safety
bounds?

## Candidate hypothesis

The candidate hypothesis predicted that CCR-VOC would outperform a calibrated
safe baseline by at least 10% in verified useful work per dollar without
violating false-acceptance, budget, or terminal-state constraints.

## Final finding

The hypothesis was not supported. After a bounded repair cycle, both known- and
learned-model CCR-VOC accepted 0 of 1,000 disjoint-test tasks and produced zero
verified useful work per dollar. Productive baselines existed, but their
false-acceptance rates exceeded the 5% requirement. Four of five diagnostic
scale-up gates failed, so a larger run was not justified.

| Policy | Test acceptances | Test FAR | Test VUD | Interpretation |
| --- | ---: | ---: | ---: | --- |
| CCR-VOC, known model | 0/1,000 | not estimable as safe | 0.0000 | Abstention collapse |
| CCR-VOC, learned model | 0/1,000 | not estimable as safe | 0.0000 | Abstention collapse |
| Fixed compute | 207/1,000 | 14.98% | 0.2021 | Productive, unsafe |
| Greedy confidence | 73/1,000 | 12.33% | 0.0940 | Productive, unsafe |

Zero acceptances are not evidence of safety: with no accepted trials, the
one-sided false-acceptance upper bound is 1.0.

## Why the negative result matters

The experiment distinguishes productivity from safety and rejects scale-up
when mechanism failure—not sample size—is limiting. It shows a workflow capable
of testing its own proposal, finding implementation defects, repairing them,
and still rejecting the repaired hypothesis when end-to-end evidence fails.

This result does **not** prove that value-of-computation scheduling is
impossible, that all CCR-VOC variants fail, or that no safe productive
scheduler exists.

## Mathematical objective

For policy $\pi$, the main utility metric is verified useful work per dollar:

$$
\text{VUD}(\pi) = \frac{\sum_i u_i\,\mathbf{1}[\text{accepted}_i \land \text{oracle-correct}_i]}{\sum_i \text{cost}_i}
$$

The candidate policy must improve VUD while meeting false-acceptance risk
bounds. Hidden oracle correctness is available to evaluation only, never to a
policy.

## Simulator capabilities

- heterogeneous tasks and agent competence;
- hidden oracle correctness;
- correlated agent and verifier failures;
- evidence invalidation after candidate mutation;
- stochastic costs and durations;
- hard budgets and deadlines;
- diminishing returns;
- repairs and repair-induced regressions;
- known-model and learned-model policy modes;
- propensity logging and overlap diagnostics;
- disjoint training, calibration, and test splits;
- nominal and adversarial regimes.

## Policies and baselines

The harness implements CCR-VOC in known- and learned-model modes, fixed compute,
fixed retry, generate-and-review, greedy confidence, epsilon bandit, Thompson
sampling, UCB1, linear Thompson sampling, and LinUCB. The bounded repair
diagnostic compares the two CCR-VOC modes with fixed compute and greedy
confidence.

## Experimental methodology

The completed workflow separated model training, threshold calibration, and
final testing. Policy thresholds were frozen before the disjoint test.
Bonferroni-adjusted upper confidence bounds were used during calibration.
Budget and terminal-state invariants were checked independently of statistical
performance. Publication review also corrected a Python set-order dependency in
agent-family shock assignment and added a cross-process regression test. See
[the methodology](docs/methodology.md) for details.

## Executed results

The bounded diagnostic used 2,000 training tasks, 1,500 calibration tasks, and
1,000 disjoint-test tasks. Learned CCR-VOC accepted 3 calibration tasks, one
incorrect, for an adjusted FAR upper bound of 0.934. Known-model CCR-VOC
accepted none. Only the combined budget and terminal-state invariant gate
passed:

| Gate | Result |
| --- | --- |
| Calibration acceptance support | FAIL |
| Safe baseline exists | FAIL |
| Nonzero CCR-VOC VUD | FAIL |
| Risk calibration | FAIL |
| Budget and terminal invariants | PASS |

The original fast experiment also ended `PARTIAL`; its frozen report and
machine-readable outputs remain in [`artifacts/`](artifacts/).

## Interpretation and failure analysis

The conservative planner collapsed into abstention. The learned policy also
lacked enough accepted calibration examples to support a useful risk estimate.
Increasing task counts would not repair the planning horizon, value estimator,
or calibration-support problem visible at the current scale. Fixed compute and
greedy confidence demonstrated that the environment permits useful work, but
neither met the safety constraint.

The detailed account is in
[`docs/negative-result.md`](docs/negative-result.md).

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/ccrvoc/` | Simulator, policies, calibration, metrics, and reporting |
| `configs/` | Default, fast, full, and bounded-diagnostic configurations |
| `tests/` | Behavioral, statistical, leakage, and invariant tests |
| `artifacts/` | Frozen reports, tables, plots, and task-level outputs |
| `docs/` | Methodology and negative-result interpretation |
| `scripts/` | Convenience entry points for fast and full runs |

## Reproduction

Python 3.12 and [`uv`](https://docs.astral.sh/uv/) are required.

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src
```

Reproduce the bounded diagnostic in a new output directory:

```bash
MPLCONFIGDIR=/tmp/ccrvoc-mpl \
uv run ccrvoc diagnostic \
  --config configs/diagnostic.yaml \
  --output reproduced/repair_diagnostic
```

The completed diagnostic took approximately 255 seconds in its recorded
environment. The original fast experiment took approximately 88 minutes. The
full configuration was not run because the scale-up gates failed.

The general experiment and report-finalization commands are:

```bash
MPLCONFIGDIR=/tmp/ccrvoc-mpl \
uv run ccrvoc run --config configs/fast.yaml --output reproduced/fast

uv run ccrvoc finalize \
  --config configs/fast.yaml \
  --output reproduced/fast \
  --executed-commit <commit-sha>
```

## Artifact index

- [`artifacts/final_report.md`](artifacts/final_report.md): original experiment report and repair addendum
- [`artifacts/acceptance_checklist.json`](artifacts/acceptance_checklist.json): original acceptance gates
- [`artifacts/policy_summary.csv`](artifacts/policy_summary.csv): original policy metrics
- [`artifacts/calibration_results.csv`](artifacts/calibration_results.csv): original calibration sweep
- [`artifacts/repair_diagnostic/repair_report.md`](artifacts/repair_diagnostic/repair_report.md): bounded diagnostic report
- [`artifacts/repair_diagnostic/gate_checklist.json`](artifacts/repair_diagnostic/gate_checklist.json): diagnostic scale-up gates
- [`artifacts/repair_diagnostic/policy_summary.csv`](artifacts/repair_diagnostic/policy_summary.csv): disjoint-test policy metrics
- [`artifacts/plots/`](artifacts/plots/): generated plots
- [`docs/publication-verification.md`](docs/publication-verification.md): independent publication checks and reproducibility repair
- Parquet files in `artifacts/`: task-level machine-readable results

## Limitations

- All evidence is generated inside a declared synthetic model.
- The experiment does not establish real-world agent performance.
- The current planner uses a shallow finite planning horizon.
- Calibration support collapses when a policy rarely accepts.
- Results are conditional on the implemented task, failure, cost, and deadline distributions.
- The public snapshot records the original and repaired source commit identifiers, while publication documentation and frozen artifacts were added afterward.

## Potential future research

The next bounded question is:

> Does any policy using the available actions, observations, budgets, and
> deadlines achieve positive useful-work coverage with a statistically
> supported false-acceptance rate of at most 5%?

That experiment is proposed, not completed. It should first establish whether
the environment admits any safe productive policy before investing in another
CCR-VOC redesign.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

## License

The code and documentation are released under the [MIT License](LICENSE).
Generated experimental artifacts are included for reproducibility and should be
interpreted with the limitations above.
