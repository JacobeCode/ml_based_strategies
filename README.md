# ML_Based_Strategies

STALKER A-Life–inspired simulation of factions and NPCs, with ML/statistical decision models. Prototype in Python, designed to be ported to a game engine later.

## In progress

**Sim**
- Simulation grounds: a location-graph world (`data/worlds/`: `factions.toml`, `locations.toml`, `paths.toml`, `threats.toml`; code in `world/`), and a Plotly view (`viz/`, style in `data/viz/style.toml`). Run `uv run python -m ml_based_strategies.main`, then open `out/world.html` with Live Preview.

**Container hardening**
- (nothing active)

## To do

**Sim**
- [ ] Squads/NPCs placed on the map, with snapshots over ticks
- [ ] Time system: `advance(time_points)`, with fine ticks for NPC life, coarse passes for factions, and a fixed world calendar
- [ ] `decide(state, options) -> {choice, probs}`: utility AI with a softmax as the baseline, then local Ollama for factions, a small classifier for NPCs, and distillation
- [ ] Rules from data as action masking before `decide()` (started: `World.can_enter`)
- [ ] Design for long time skips
- [ ] Notebook setup (`ipykernel`) for Plotly analysis
- [ ] Graph algorithms for the sim:
  - shortest travel paths (Dijkstra on `cost`)
  - routes limited to what a faction may enter (`can_enter`)
  - chokepoints

  When this starts, pull the connectivity flood fill out of `WorldSpec._check_graph` into a shared `reachable(adjacency_dict, start)` helper in `world/`. Decide stdlib vs `networkx` then; today `networkx` is only pulled in by torch, in the `train` group.

**Container hardening** (fixed as issues come up)
- [ ] Narrow the workspace mount: `../..` exposes sibling host projects
- [ ] Try `/sandbox` for Claude Code and check whether it blocks the VS Code socket (`$BROWSER`, `code`)
- [x] Decide on git credential and SSH agent forwarding: stay on SSH, keep agent forwarding (keys stay on the host)
- [ ] Clean up the WSL host shell setup: tidy the `keychain` agent line in `~/.bashrc` and remove the broken `/bin/brew` line from the rc files
- [x] Port clash: Live Preview moved to 5500, Grafana keeps 3000
- [ ] `just monitor-open` can't open anything from inside the container
- [ ] Back up the `claude-config` volume (Claude memory and login), which is lost on `docker volume prune`

**Other**
- [ ] Fedora setup for Distro

## Status

Early prototype: a world map loads and renders. No agents, ticks or decision models yet.

## Environment

| Item | Value |
|------|-------|
| Python | 3.12 (pinned via `.python-version`) |
| Package manager | `uv` |
| Virtual env | `.venv/` |
| Dev container | Docker Compose (`.devcontainer/`) — services: `dev`, `ollama`, `model-init` |
| GPU | passthrough on `dev` (NVIDIA Container Toolkit required on host) |
| Monitoring | Grafana/Prometheus/Loki, opt-in via `just monitor-up` (not part of `docker compose up`); Grafana on `127.0.0.1:3000` (Live Preview on `5500`/`5501` to avoid a clash) |

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
├── AGENTS.md                   # agent guidance (tool-agnostic, source of truth)
├── CLAUDE.md                   # imports AGENTS.md for Claude Code
├── pyproject.toml
├── uv.lock
├── .python-version
└── README.md
```

See `AGENTS.md` for agent conventions and the security/tooling setup.
