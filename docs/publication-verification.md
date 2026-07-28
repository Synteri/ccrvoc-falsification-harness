# Publication verification

Date: 2026-07-28

## Source provenance

- Original restored source commit: `91427a6da551a0873b789f097ddc1c1a180d931b`
- Bounded repair diagnostic source commit: `227ac67736458734db07d28a3907a8eef986f6f8`
- Diagnostic status: `PARTIAL`
- Larger run authorized: `false`

## Quality checks

Executed from the repository root:

```bash
UV_CACHE_DIR=/tmp/ccrvoc-publish-uv uv sync --locked --extra dev
UV_CACHE_DIR=/tmp/ccrvoc-publish-uv uv run ruff format --check .
UV_CACHE_DIR=/tmp/ccrvoc-publish-uv uv run ruff check .
UV_CACHE_DIR=/tmp/ccrvoc-publish-uv uv run mypy src
UV_CACHE_DIR=/tmp/ccrvoc-publish-uv \
MPLCONFIGDIR=/tmp/ccrvoc-publish-mpl \
uv run pytest -q
```

Results:

- locked dependency installation passed;
- Ruff formatting passed;
- Ruff lint passed;
- mypy passed for 34 source files;
- 34 tests passed.

## Diagnostic reproduction

The bounded diagnostic was rerun into an isolated temporary directory:

```bash
UV_CACHE_DIR=/tmp/ccrvoc-publish-uv \
MPLCONFIGDIR=/tmp/ccrvoc-publish-mpl \
uv run ccrvoc diagnostic \
  --config configs/diagnostic.yaml \
  --output /tmp/ccrvoc-publication-final-reproduction
```

The rerun returned `PARTIAL`. These outputs matched the frozen artifacts
exactly:

- `calibration.csv`;
- `gate_checklist.json`;
- `overlap_diagnostics.json`;
- `config_resolved.yaml`;
- every `policy_summary.csv` field except measured scheduler wall-clock time;
- every `test_results.parquet` field except measured scheduler wall-clock time.

Scheduler timing is intentionally excluded from exact comparison because it is
a measured performance value and varies by machine and process load.

## Reproducibility defect found during review

The first publication rerun exposed Python hash-order dependence in
agent-family shock assignment. An unordered `set` could swap which deterministic
random draw was assigned to each family. The public source uses stable
first-seen family order and includes a regression test that compares subprocess
outputs under multiple `PYTHONHASHSEED` values.

## Security and privacy checks

The latest tree, frozen artifacts, binary string tables, and available Git
history were searched for:

- common API-key and token formats;
- password, credential, and private-key markers;
- authorization headers and cookies;
- absolute workspace and user-home paths;
- personal email addresses;
- machine-specific Windows user paths.

No suspected secret, personal path, or personal email exposure was found.
Repository history uses generic Codex author identities. No dedicated secret
scanner was installed in the publication environment, so this was a structured
pattern and history scan rather than a vendor-backed scan.

## Claim boundary

Publication verifies a negative result inside the declared synthetic model. It
does not establish novelty, real-world safety, commercial viability, or the
impossibility of safe productive value-of-computation scheduling.
