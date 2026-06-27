# Contributing

Thanks for helping improve AI Research Radar. Keep changes focused, tested,
and consistent with the existing CLI-first, offline-friendly core.

## How to contribute

### Setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

### Run tests

```bash
python -m pytest -q
```

Pull requests run the same flow in CI: editable install with dev extras, a
quick `radar` smoke check, then pytest.

### Open a PR

1. Branch from `main` with a descriptive name.
2. Add or update tests when behavior changes.
3. Confirm tests pass locally.
4. Open a pull request against `main` with a short summary of what changed and
   why.

For config keys and architecture notes, see [docs/config.md](docs/config.md) and
the ADRs under [docs/](docs/).
