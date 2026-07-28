from copy import deepcopy

import pytest

from ccrvoc.config import validate_config


def test_fast_config_exact_sizes(config: dict) -> None:
    assert config["sizes"] == {
        "training": 10_000,
        "validation": 3_000,
        "calibration": 5_000,
        "nominal_seeds": 3,
        "nominal_tasks_per_seed": 500,
        "adversarial_seeds": 2,
        "adversarial_tasks_per_seed": 500,
    }


def test_particle_count_cannot_be_silently_reduced(config: dict) -> None:
    bad = deepcopy(config)
    bad["particles"] = 299
    with pytest.raises(ValueError):
        validate_config(bad)
