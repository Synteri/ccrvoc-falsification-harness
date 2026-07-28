from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def _load_unvalidated(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text()) or {}
    parent = data.pop("extends", None)
    if parent:
        parent_path = (path.parent / parent).resolve()
        data = _merge(_load_unvalidated(parent_path), data)
    return data


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path).resolve()
    data = _load_unvalidated(path)
    validate_config(data)
    return data


def validate_config(cfg: dict[str, Any]) -> None:
    required = {"seed", "mode", "particles", "ensemble_members", "sizes", "action_means"}
    missing = required - cfg.keys()
    if missing:
        raise ValueError(f"missing config keys: {sorted(missing)}")
    if cfg["mode"] not in {"fast", "full"}:
        raise ValueError("mode must be fast or full")
    expected = 300 if cfg["mode"] == "fast" else 2000
    if cfg["particles"] != expected:
        raise ValueError(f"{cfg['mode']} mode requires {expected} particles")
    if cfg["ensemble_members"] != (4 if cfg["mode"] == "fast" else 16):
        raise ValueError("wrong ensemble member count for mode")
    if not 0 < cfg["cost_cv"] < 1 or not 0 < cfg["duration_cv"] < 1:
        raise ValueError("coefficients of variation must lie in (0,1)")
