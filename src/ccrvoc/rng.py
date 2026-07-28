from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

STREAMS = (
    "task_generation",
    "actual_agent_outcomes",
    "actual_evidence_outcomes",
    "action_costs",
    "durations",
    "policy_posterior_sampling",
    "causal_model_training",
    "bootstrap_analysis",
)


def named_seed(root_seed: int, *parts: object) -> int:
    payload = "|".join([str(root_seed), *(str(p) for p in parts)]).encode()
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def generator(root_seed: int, stream: str, *parts: object) -> np.random.Generator:
    if stream not in STREAMS:
        raise ValueError(f"unknown RNG stream: {stream}")
    return np.random.default_rng(named_seed(root_seed, stream, *parts))


@dataclass(frozen=True)
class EpisodeRNG:
    root_seed: int
    task_id: int
    world: int = 0

    def get(self, stream: str, *parts: object) -> np.random.Generator:
        return generator(self.root_seed, stream, self.world, self.task_id, *parts)
