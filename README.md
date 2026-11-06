# ML_Based_Strategies

For fill later.

## Status

Skeleton only — `src/ml_based_strategies/main.py` is the sole source file (a stub entry point). No models, datasets, or experiments yet.

## Environment

| Item | Value |
|------|-------|
| Python | 3.12 (pinned via `.python-version`) |
| Package manager | `uv` |
| Virtual env | `.venv/` |
| Dev container | Docker Compose (`.devcontainer/`) — services: `dev`, `ollama`, `model-init` |
| GPU | passthrough on `dev` (NVIDIA Container Toolkit required on host) |
| Monitoring | Grafana/Prometheus/Loki, opt-in via `just monitor-up` (not part of `docker compose up`) |

## Dependencies (`pyproject.toml`)

- `pytest` + `pytest-cov` — testing + total coverage gate
- `coverage-threshold` — per-file coverage floor
- `ruff` — linting + formatting (line-length 120, rules `E`/`F`/`I`/`UP`/`B` — replaces black/isort/pycodestyle/pyflakes as separate tools)
- `pre-commit` — the hooks below, installed automatically on container start
- `torch` / `torchvision` — CUDA build, from the `pytorch-cuxxx` index (verify against `pytorch.org/get-started/locally/`, not PyPI's default CPU build)

## Setup

Open in VS Code → "Reopen in Container." `uv sync` and the pre-commit hooks run automatically via `.devcontainer/post-create.sh`.

## Commands

```bash
uv sync                                              # install dependencies
uv run python src/ml_based_strategies/main.py   # run the entry point

just test                                            # uv run pytest (+ coverage)
just lint                                            # ruff check --fix, then ruff format
uv run pre-commit run --all-files                    # run all hooks manually
just scan [target]                                   # SkillSpector (static + LLM)
just ask <question>                                  # one-shot local-model query
just model-off                                        # free the model's GPU memory before training
just model-on                                         # load it back after training
just gpu                                              # verify CUDA is visible
just monitor-up                                      # start the usage dashboard (Grafana @ :3000)
just monitor-down                                    # stop it
```

Run `just --list` for the full set.

### Executable scripts (AD. just)

Generated projects run scripts directly (`./scripts/model.sh`, via `just`), so they need the executable bit. Cookiecutter copies file modes as they are in the template checkout, and `post_gen_project.py` adds the bit as a safety net (only to `.sh` files in `scripts/` and `.devcontainer/` that start with `#!`). The source of truth is still git: record the mode when you add or change a directly-run script, so the template is correct on its own. Without it, a checkout on a filesystem without Unix modes (for example a Windows mount) hands the hook scripts with the wrong mode, and the hook has to repair every bake:

```bash
git add --chmod=+x "ml_based_strategies/scripts/new-script.sh"     # new file
git update-index --chmod=+x "ml_based_strategies/scripts/old.sh"  # already tracked
git ls-files -s "ml_based_strategies/scripts"                     # 100755 = executable
```

Sourced helpers without a `#!` line (such as `logging.sh`) stay non-executable on purpose.

## Quality gates (pre-commit)

1. Hygiene: trailing whitespace, EOF newline, large files, private keys, debug-statement detection (leftover `pdb`/`breakpoint()`; it does not flag `print()`).
2. JSON/YAML validation
3. `ruff-check` (`--fix`), then `ruff-format` — in that order, since fixes can produce code that needs reformatting
4. `uv-lock` — keeps `uv.lock` in sync with `pyproject.toml`
5. `blacken-docs` — formats Python code blocks in markdown docs
6. `skillspector-static` — static-only (`--no-llm`) scan of `./skills/`; the LLM pass is on-demand (`just scan`), never on every commit
7. `pytest` (total coverage, `fail_under`) → `coverage json` → `coverage-threshold` (per-file floor) — in that order, since `coverage-threshold` reads the JSON report

This is not `fail_fast` — a single commit attempt reports every failing hook, not just the first.

## Project layout

```
ml_based_strategies/
├── .devcontainer/
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   └── post-create.sh
├── .continue/
│   └── config.yaml
├── src/ml_based_strategies/
│   ├── __init__.py
│   ├── main.py                # stub entry point
│   ├── test/
│        └── test_smoke.py
├── scripts/
│   ├── logging.sh             # shared log/warn/err
│   ├── scan.sh
│   ├── ask.sh
│   └── model.sh
├── logs/                       # gitignored, truncated per run
├── skills/
├── .pre-commit-config.yaml
├── .github/workflows/
│   ├── skill-scan.yml
│   └── ci.yml
├── .gitignore
├── .dockerignore
├── .env                        # gitignored, real values
├── .env.example                # committed, durable reference
├── justfile
├── CLAUDE.md                   # guidance for Claude Code
├── pyproject.toml
├── uv.lock
├── .python-version
└── README.md
```

See `CLAUDE.md` for agent-specific conventions and the security/tooling setup.