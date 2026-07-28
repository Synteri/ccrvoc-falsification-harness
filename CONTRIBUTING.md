# Contributing

Contributions that improve reproducibility, add independently justified
baselines, strengthen statistical tests, or identify modeling defects are
welcome.

Before opening a pull request:

```bash
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
```

Please separate simulator corrections from policy improvements. Changes that
alter an executed configuration, metric, statistical gate, or frozen artifact
must explain the scientific impact and must not overwrite the original
evidence. New experimental outputs should use a new directory and identify the
source commit and resolved configuration.

Do not describe a generated result as validated, reviewed, approved, or
published unless the corresponding checks have actually occurred.
