from pathlib import Path

import pytest

from ccrvoc.config import load_config


@pytest.fixture(scope="session")
def config() -> dict:
    return load_config(Path("configs/fast.yaml"))
