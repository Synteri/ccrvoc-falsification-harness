from ccrvoc.policies.base import ScheduledPolicy


class FixedComputePolicy(ScheduledPolicy):
    name = "fixed_compute"
    schedule = (
        "context",
        "generate",
        "unit_test",
        "integration_test",
        "fuzz_security",
        "independent_review",
        "spec_review",
        "adversarial_review",
    )
