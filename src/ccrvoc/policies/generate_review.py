from ccrvoc.policies.base import ScheduledPolicy


class GenerateReviewPolicy(ScheduledPolicy):
    name = "generate_review"
    schedule = ("generate", "independent_review")
