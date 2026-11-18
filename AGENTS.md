# AGENTS.md

Guidance for coding agents (Claude Code, Continue, Codex, …) working in this repository.

## Environment

- GPU training: the `dev` service has GPU passthrough; `ollama` uses the GPU too — run `just model-off` before training and `just model-on` after, otherwise it keeps its VRAM and training may OOM. Verify with `just gpu`.
- `logs/` is gitignored and truncated at the start of each run, so only the most recent run is kept.

## Code style

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
- Grafana listens on `127.0.0.1:3000`; VS Code Live Preview is moved to `3001` (`livePreview.portNumber` in `devcontainer.json`) so they don't clash — don't put anything else on 3000. `just monitor-open` can't launch a browser from inside the container — give the user the URL instead.
- No local-model panel: Ollama usage (tokens/latency) is not monitored.
- Prompt/response text capture is off by default (`OTEL_LOG_USER_PROMPTS`/`OTEL_LOG_RAW_API_BODIES` in `.env`, both unset) — turn on deliberately, not something to flip without thinking about what it captures.
