# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`ml_based_strategies` — For fill later.

## Environment

- **Dev container**: Docker Compose–based devcontainer (`.devcontainer/`), services: `dev` (this container), `ollama` (local model, CPU-served), `model-init` (one-shot model pull). Open in VS Code → "Reopen in Container."
- Python >=3.12 (managed via `uv`, see `uv.lock` and `pyproject.toml`)
- Install dependencies: `uv sync` (also runs automatically via `post-create.sh` on container start)
- GPU training: the `dev` service has GPU passthrough; `ollama` uses the GPU too — run `just model-off` before training and `just model-on` after. Verify with `just gpu`.

## Commands

- Run tests: `just test`
- Lint + format: `just lint`
- Run pre-commit hooks manually: `uv run pre-commit run --all-files`
- Scan skills: `just scan [target]` (static always; LLM pass uses the local model)
- Ask the local model (one-shot): `just ask <question>`
- Chat with memory: Continue CLI (`cn`) — use `.continue/config.yaml`
- Train: run your training command directly — first `just model-off` (frees the GPU from the local model), then `just model-on` after
- Usage/cost dashboard: `just monitor-up` (Grafana at `localhost:3000`), `just monitor-down` when done — off by default, not part of `docker compose up`

## Structure

- `src/ml_based_strategies/` — the package.
- `src/test/` — test suite.
- `scripts/` — `scan.sh` (SkillSpector), `ask.sh` (local model), `model.sh` (free/restore the model around training), `logging.sh` (shared log/warn/err, sourced by the others).
- `skills/` — third-party agent skills. **Every skill here is scanned by SkillSpector before use** — see Security below.
- `logs/` — per-script run logs. Gitignored; truncated at the start of each run, so only the most recent run is kept.
- `.continue/config.yaml` — points Continue (editor extension + `cn` CLI) at the local model.
- `monitoring/` — Prometheus + Grafana config for the optional usage dashboard.

## Code style

- Ruff: `line-length = 120`, rule sets `E`, `F`, `I`, `UP`, `B`.
- Coverage — two separate gates:
  - Total: `[tool.coverage.report] fail_under` — enforced automatically via `pytest`'s `--cov`.
  - Per-file: `coverage-threshold` (separate tool; top-level `[coverage-threshold]` table) — reads `coverage.json`, so it's `coverage json -q && coverage-threshold`, not standalone.

## Pre-commit

- Hygiene: JSON/YAML checks, EOF fixer, trailing whitespace, private-key detection, large-file guard, debug-statement detection (leftover `pdb`/`breakpoint()`; it does not flag `print()`).
- `ruff-check` (`--fix`) then `ruff-format`.
- `uv-lock` — keeps `uv.lock` in sync with `pyproject.toml`.
- `blacken-docs` — formats Python code blocks in markdown docs.
- `skillspector-static` — static-only (`--no-llm`) scan of `./skills/`; the LLM pass is on-demand (`just scan`), never on every commit.
- `pytest` (total coverage) → `coverage json` → `coverage-threshold` (per-file), in that order.

## Security

- Third-party skills in `./skills/` are gated by SkillSpector. Contract: exit `0` = SAFE/CAUTION, exit `1` = DO_NOT_INSTALL, exit `2` = scan error. Don't bypass a failing scan.
- Don't run with `--dangerously-skip-permissions`.
- Agent tooling: CodeGraph (query the graph before reading files to understand structure — this is where its value is realized), Ponytail (write-less-code discipline), Headroom (token compression). Third-party; pinned versions in `post-create.sh`.

## Style

- Prefer the standard library and native features over new dependencies.
- Smallest change that works; don't add speculative abstraction.
- Never sacrifice input validation, error handling, security, or accessibility.

## Local model

- Served by the `ollama` service, warm by default (`OLLAMA_KEEP_ALIVE=-1`) so scans/chat are instant, no cold start. It runs on the GPU — check with `docker compose exec ollama ollama ps`.
- Free it by hand for training: `just model-off` before, `just model-on` after — otherwise it keeps its VRAM and training may OOM. Anything that queries it mid-run (Continue autocomplete) reloads it, so turn autocomplete off for long runs.

## Monitoring

- Cost, token, and tool-call dashboards (Claude Code's own OTel export — works under subscription login, not just an API key). `just monitor-up` to start, `just monitor-down` to stop; not running unless you start it.
- No local-model panel: Ollama usage (tokens/latency) is not monitored.
- Prompt/response text capture is off by default (`OTEL_LOG_USER_PROMPTS`/`OTEL_LOG_RAW_API_BODIES` in `.env`, both unset) — turn on deliberately, not something to flip without thinking about what it captures.