# CCR-VOC bounded repair diagnostic

## Outcome

The bounded repair diagnostic did not pass its gates.
Accordingly, a second fast or full experiment is **not authorized**.
This diagnostic is not a validation of the master hypothesis.

## Reproducibility

- Commit: `227ac67736458734db07d28a3907a8eef986f6f8`
- Command:
  `UV_CACHE_DIR=/tmp/ccrvoc-repair-uv MPLCONFIGDIR=/tmp/ccrvoc-mpl`
  `uv run ccrvoc diagnostic --config configs/diagnostic.yaml`
  `--output artifacts/repair_diagnostic`
- Elapsed seconds: 254.925
- Resolved diagnostic sizes: `{"calibration": 1500, "test": 1000, "training": 2000}`
- Threshold grid: `[0.05, 0.1, 0.15, 0.2]`
- Estimator: inverse-propensity-weighted logistic transition model

## Frozen calibration choices

```json
{
  "ccr_voc_known": {
    "confidence": 0.9875,
    "safe": false,
    "threshold": 0.05
  },
  "ccr_voc_learned": {
    "confidence": 0.9875,
    "safe": false,
    "threshold": 0.2
  },
  "fixed_compute": {
    "confidence": 0.9875,
    "safe": false,
    "threshold": 0.2
  },
  "greedy_confidence": {
    "confidence": 0.9875,
    "safe": false,
    "threshold": 0.2
  }
}
```

## Gates

- FAIL — calibration_acceptance_support: `{"pass": false, "required_per_policy": 100, "selected_acceptances": {"ccr_voc_known": 0, "ccr_voc_learned": 3, "fixed_compute": 321, "greedy_confidence": 104}}`
- FAIL — safe_baseline_exists: `{"pass": false, "safe_baselines": []}`
- FAIL — nonzero_vud: `{"pass": false, "vud": {"ccr_voc_known": 0.0, "ccr_voc_learned": 0.0, "fixed_compute": 0.20206405839593905, "greedy_confidence": 0.0940478841534571}}`
- FAIL — risk_calibration: `{"pass": false, "selected_policy_calibrations": {"ccr_voc_known": {"confidence": 0.9875, "safe": false, "threshold": 0.05}, "ccr_voc_learned": {"confidence": 0.9875, "safe": false, "threshold": 0.2}, "fixed_compute": {"confidence": 0.9875, "safe": false, "threshold": 0.2}, "greedy_confidence": {"confidence": 0.9875, "safe": false, "threshold": 0.2}}}`
- PASS — budget_and_terminal_invariants: `{"budget_violations": 0, "pass": true, "post_terminal_attempts": 0}`

## Calibration results

```csv
policy,threshold,tasks,accepted,incorrect,far,far_upper_bonferroni,vud,safe,split
fixed_compute,0.05,1500,0,0,0.0,1.0,0.0,False,calibration
fixed_compute,0.1,1500,9,4,0.4444444444444444,0.8199871834162615,0.004192378123809054,False,calibration
fixed_compute,0.15,1500,93,20,0.21505376344086022,0.3264283873012514,0.06457039428855083,False,calibration
fixed_compute,0.2,1500,321,65,0.20249221183800623,0.2576702425239927,0.19047676276825282,False,calibration
greedy_confidence,0.05,1500,0,0,0.0,1.0,0.0,False,calibration
greedy_confidence,0.1,1500,0,0,0.0,1.0,0.0,False,calibration
greedy_confidence,0.15,1500,46,6,0.13043478260869565,0.2821428887584837,0.043189928151472746,False,calibration
greedy_confidence,0.2,1500,104,15,0.14423076923076922,0.238921605534201,0.08582070693025096,False,calibration
ccr_voc_known,0.05,1500,0,0,0.0,1.0,0.0,False,calibration
ccr_voc_known,0.1,1500,0,0,0.0,1.0,0.0,False,calibration
ccr_voc_known,0.15,1500,0,0,0.0,1.0,0.0,False,calibration
ccr_voc_known,0.2,1500,0,0,0.0,1.0,0.0,False,calibration
ccr_voc_learned,0.05,1500,0,0,0.0,1.0,0.0,False,calibration
ccr_voc_learned,0.1,1500,0,0,0.0,1.0,0.0,False,calibration
ccr_voc_learned,0.15,1500,0,0,0.0,1.0,0.0,False,calibration
ccr_voc_learned,0.2,1500,3,1,0.3333333333333333,0.9339810982694496,0.004384973101399638,False,calibration
```

## Disjoint-test policy summary

```csv
policy,vud,correct_utility_per_task,far,severity_weighted_far,acceptance_coverage,correct_acceptance_rate,failure_declaration_rate,cost_per_task,cost_per_correct_task,deadline_miss_rate,budget_violation_rate,scheduler_overhead_seconds,stale_evidence_invalidations,accepted,false_accepts,tasks,far_upper_95,terminal_action_count
ccr_voc_known,0.0,0.0,0.0,0.0,0.0,0.0,1.0,1.5346846324041759,1534.6846324041758,0.029,0.0,11.826494339005421,3737.0,0.0,0.0,1000.0,1.0,0
ccr_voc_learned,0.0,0.0,0.0,0.0,0.0,0.0,1.0,1.4063984522001916,1406.3984522001915,0.017,0.0,18.01388408899652,3193.0,0.0,0.0,1000.0,1.0,0
fixed_compute,0.20206405839593905,0.298716314287444,0.1497584541062802,0.17595541401273887,0.207,0.176,0.793,1.4783248275758052,8.399572883953438,0.039,0.0,0.28570243200533696,0.0,207.0,31.0,1000.0,0.19671988035766477,0
greedy_confidence,0.0940478841534571,0.1368063818550949,0.1232876712328767,0.11407766990291261,0.073,0.064,0.927,1.454646035756308,22.728844308692313,0.094,0.0,1.123823000989205,3206.0,73.0,9.0,1000.0,0.2052790964960025,0
```

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
