import pandas as pd

from ccrvoc.diagnostic import evaluate_diagnostic_gates


def test_diagnostic_gates_reject_zero_acceptance() -> None:
    calibration = pd.DataFrame(
        [
            {
                "policy": name,
                "threshold": 0.1,
                "accepted": 0,
            }
            for name in (
                "fixed_compute",
                "greedy_confidence",
                "ccr_voc_known",
                "ccr_voc_learned",
            )
        ]
    )
    summary = pd.DataFrame(
        [
            {
                "policy": name,
                "vud": 0.0,
                "budget_violation_rate": 0.0,
                "terminal_action_count": 0,
            }
            for name in (
                "fixed_compute",
                "greedy_confidence",
                "ccr_voc_known",
                "ccr_voc_learned",
            )
        ]
    )
    chosen = {
        name: {"threshold": 0.1, "safe": False, "confidence": 0.9875}
        for name in (
            "fixed_compute",
            "greedy_confidence",
            "ccr_voc_known",
            "ccr_voc_learned",
        )
    }
    gates = evaluate_diagnostic_gates(calibration, summary, chosen)
    assert not gates["calibration_acceptance_support"]["pass"]
    assert not gates["safe_baseline_exists"]["pass"]
    assert not gates["nonzero_vud"]["pass"]
    assert not gates["risk_calibration"]["pass"]
    assert gates["budget_and_terminal_invariants"]["pass"]
