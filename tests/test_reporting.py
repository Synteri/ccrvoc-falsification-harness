import pandas as pd

from ccrvoc.reporting import markdown_table


def test_action_count_dictionary_is_not_numeric_action_column() -> None:
    frame = pd.DataFrame(
        {
            "action_counts": [{"unit_test": 1}, {"unit_test": 2}],
            "action_unit_test": [1, 2],
        }
    )
    columns = [
        c for c in frame if c.startswith("action_") and pd.api.types.is_numeric_dtype(frame[c])
    ]
    assert columns == ["action_unit_test"]


def test_markdown_table_has_no_optional_dependency() -> None:
    table = markdown_table(pd.DataFrame({"name": ["a|b"], "value": [1.25]}))
    assert "a\\|b" in table
    assert "| name | value |" in table
