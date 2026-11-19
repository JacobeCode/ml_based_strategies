# AGENTS.md

Guidance for coding agents (Claude Code, Continue, Codex, …) working in this repository.

## Environment

- GPU training: the `dev` service has GPU passthrough; `ollama` uses the GPU too — run `just model-off` before training and `just model-on` after, otherwise it keeps its VRAM and training may OOM. Verify with `just gpu`.
- `logs/` is gitignored and truncated at the start of each run, so only the most recent run is kept.

## Code style

- Docstrings: opening and closing `"""` on their own lines, even for one-liners:

  ```python
  """
  Load and validate a world directory.
  """
  ```

- Naming: suffix container and frame variables with their type, so it's clear at a glance what you're holding:

  | Type | Suffix | Example |
  |---|---|---|
  | `dict` | `_dict` | `locations_dict` |
  | `list` | `_lst` | `loc_ids_lst` |
  | `set` / `frozenset` | `_set` | `seen_set` |
  | `tuple` | `_tup` | `node_traces_tup` |
  | pandas `DataFrame` | `_df` | `episodes_df` |
  | pandas `Series` | `_ser` | `rewards_ser` |
  | Spark `DataFrame` | `_sdf` | `episodes_sdf` |
  | NumPy array | `_arr` | `features_arr` |
  | torch tensor | `_ten` | `logits_ten` |

  - Applies to variables, parameters, constants (`DEFAULTS_DICT`) and runtime attributes (`World.locations_dict`).
  - Not applied to:
    - scalars, model instances, `Path`s, figures, or single-item loop variables (`loc`, `p`)
    - pydantic schema fields that mirror data-file keys (`WorldSpec.factions`, `Faction.allowed_kinds`): the TOML is the contract
  - When renaming, don't touch method calls (`.items()`) or prose in strings and comments.
- Coverage — two separate gates:
  - Total: `[tool.coverage.report] fail_under` — enforced automatically via `pytest`'s `--cov`.
  - Per-file: `coverage-threshold` (separate tool; top-level `[coverage-threshold]` table) — reads `coverage.json`, so it's `coverage json -q && coverage-threshold`, not standalone.

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
- Anything that queries the model mid-run (Continue autocomplete) reloads it, so turn autocomplete off for long runs.
- Chat with memory: Continue CLI (`cn`), configured by `.continue/config.yaml`.

## Monitoring

- Cost, token, and tool-call dashboards (Claude Code's own OTel export — works under subscription login, not just an API key).
- Grafana listens on `127.0.0.1:3000`; VS Code Live Preview uses `5500` plus `5501` for live reload (`livePreview.portNumber` in `devcontainer.json`). Keep 3000 (Grafana), 3100 (Loki), 9090 (Prometheus) and 11434 (Ollama) free of anything else. `just monitor-open` can't launch a browser from inside the container — give the user the URL instead.
- No local-model panel: Ollama usage (tokens/latency) is not monitored.
- Prompt/response text capture is off by default (`OTEL_LOG_USER_PROMPTS`/`OTEL_LOG_RAW_API_BODIES` in `.env`, both unset) — turn on deliberately, not something to flip without thinking about what it captures.
