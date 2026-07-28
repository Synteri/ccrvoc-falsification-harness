import numpy as np

from ccrvoc.tasks import CLASS_PROBS, generate_task


def test_task_class_generation_matches_probabilities(config: dict) -> None:
    counts = np.zeros(5)
    for i in range(6000):
        counts[generate_task(config["seed"], i, {}).class_index] += 1
    assert np.max(np.abs(counts / counts.sum() - CLASS_PROBS)) < 0.025


def test_common_task_stream_is_policy_independent(config: dict) -> None:
    a = generate_task(config["seed"], 99, {})
    b = generate_task(config["seed"], 99, {})
    np.testing.assert_array_equal(a.difficulty, b.difficulty)
    np.testing.assert_array_equal(a.trap, b.trap)
    assert (a.value, a.budget, a.deadline) == (b.value, b.budget, b.deadline)
