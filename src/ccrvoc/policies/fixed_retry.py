from ccrvoc.policies.base import ScheduledPolicy


class FixedRetryPolicy(ScheduledPolicy):
    name = "fixed_retry"

    def __init__(self, config: dict, risk_threshold: float = 0.05, retries: int = 2) -> None:
        super().__init__(config, risk_threshold)
        self.retries = retries
        self.schedule = tuple(
            ["generate", "unit_test"]
            + [item for _ in range(retries) for item in ("alternative", "unit_test")]
            + ["independent_review"]
        )

    def clone(self) -> "FixedRetryPolicy":
        return type(self)(self.config, self.risk_threshold, self.retries)
