from __future__ import annotations

import numpy as np

from ccrvoc.policies.macro import MacroPolicy
from ccrvoc.types import PolicyView


class UCBPolicy(MacroPolicy):
    name = "ucb1"

    def select_arm(self, view: PolicyView) -> int:
        if (self.stats.pulls == 0).any():
            return int(np.flatnonzero(self.stats.pulls == 0)[0])
        total = self.stats.pulls.sum()
        score = self.stats.rewards / self.stats.pulls + np.sqrt(
            2 * np.log(total) / self.stats.pulls
        )
        return int(score.argmax())
