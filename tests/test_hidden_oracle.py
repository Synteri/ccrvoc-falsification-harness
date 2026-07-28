import inspect
from pathlib import Path

from ccrvoc.environment import SequentialEnvironment
from ccrvoc.policies.base import BasePolicy


def test_policy_view_contains_no_oracle_labels(config: dict) -> None:
    view = SequentialEnvironment(config, 10).view()
    assert not hasattr(view, "correct")
    assert not hasattr(view, "defects")
    assert not hasattr(view.task, "difficulty")


def test_policy_modules_do_not_reference_environment_oracle() -> None:
    policy_dir = Path("src/ccrvoc/policies")
    text = "\n".join(p.read_text() for p in policy_dir.glob("*.py"))
    assert "_oracle_correct" not in text
    assert "._candidates" not in text
    assert list(inspect.signature(BasePolicy.choose_action).parameters) == ["self", "view"]
