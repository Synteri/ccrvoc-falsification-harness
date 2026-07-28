from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


@dataclass
class OverlapDiagnostics:
    by_action: dict[str, dict[str, float]]
    minimum_propensity: float
    violations: int

    def as_dict(self) -> dict:
        return {
            "estimator": "propensity-weighted logistic transition model",
            "by_action": self.by_action,
            "minimum_propensity": self.minimum_propensity,
            "violations": self.violations,
        }


@dataclass
class LearnedCausalModel:
    models: dict[str, LogisticRegression]
    diagnostics: OverlapDiagnostics
    frozen: bool = False

    def predict_success(self, action: str, features: np.ndarray) -> float:
        model = self.models.get(action)
        if model is None:
            return 0.5
        return float(model.predict_proba(features.reshape(1, -1))[0, 1])

    def freeze(self) -> None:
        self.frozen = True

    def fit(self, _: pd.DataFrame) -> None:
        if self.frozen:
            raise RuntimeError("final testing cannot mutate frozen causal model")
        raise RuntimeError("use fit_propensity_weighted")


def fit_propensity_weighted(logs: pd.DataFrame) -> LearnedCausalModel:
    models: dict[str, LogisticRegression] = {}
    diagnostics: dict[str, dict[str, float]] = {}
    violations = 0
    for action, group in logs.groupby("action"):
        prop = group["propensity"].to_numpy(float)
        violations += int((prop < 0.05 - 1e-12).sum())
        weights = 1 / np.clip(prop, 1e-6, None)
        ess = float(weights.sum() ** 2 / np.square(weights).sum())
        diagnostics[str(action)] = {
            "n": float(len(group)),
            "ess": ess,
            "min_propensity": float(prop.min()),
        }
        for stratum, subgroup in group.groupby("stratum"):
            stratum_prop = subgroup["propensity"].to_numpy(float)
            stratum_weights = 1 / np.clip(stratum_prop, 1e-6, None)
            diagnostics[f"{action}|{stratum}"] = {
                "n": float(len(subgroup)),
                "ess": float(stratum_weights.sum() ** 2 / np.square(stratum_weights).sum()),
                "min_propensity": float(stratum_prop.min()),
            }
        x = group[["value", "budget_remaining", "elapsed_fraction", "evidence_count"]].to_numpy()
        y = group["success"].to_numpy(int)
        if len(np.unique(y)) > 1:
            model = LogisticRegression(max_iter=200)
            model.fit(x, y, sample_weight=weights)
            models[str(action)] = model
    minimum = float(logs["propensity"].min()) if len(logs) else 0.0
    return LearnedCausalModel(models, OverlapDiagnostics(diagnostics, minimum, violations))
