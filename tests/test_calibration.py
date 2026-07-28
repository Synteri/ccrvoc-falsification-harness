from scipy.stats import beta

from ccrvoc.calibration import FrozenCalibration, assert_no_test_leakage
from ccrvoc.statistics import clopper_pearson_upper


def test_clopper_pearson_matches_scipy() -> None:
    assert clopper_pearson_upper(3, 100, 0.95) == beta.ppf(0.95, 4, 97)
    assert clopper_pearson_upper(0, 100, 0.95) == beta.ppf(0.95, 1, 100)


def test_calibration_split_is_disjoint() -> None:
    frozen = FrozenCalibration("p", 0.01, (20, 21), 0.99, True)
    assert_no_test_leakage(frozen, {1, 2}, {10, 11}, {30, 31})
