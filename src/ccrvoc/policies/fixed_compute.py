from ccrvoc.policies.base import ScheduledPolicy


class FixedComputePolicy(ScheduledPolicy):
    name = "fixed_compute"
    schedule = ("context", "generate", "unit_test", "integration_test", "independent_review")
