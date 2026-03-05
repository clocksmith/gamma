# GAMMA Architecture

Canonical high-level map of runtime surfaces, tooling boundaries, and ownership.

## Runtime Surfaces

### Python CLI Runtime

- Entry point: `gamma.py`
- Core packages:
- `src/core/` shared interfaces, routing helpers, validation
- `src/game/` CLI gameplay + tutorial + displays
- `src/mind_meld/` multi-model generation strategies
- `src/engines/` engine backends and wrappers
- `src/benchmarks/` Python benchmark runners

### Web Runtime (No Build Contract)

- Source of truth: `web/`
- Entrypoint: `web/index.html` + static ES modules
- Styling: `web/styles/`
- Deploy target: Firebase Hosting from `web/`
- Contract: do not check in generated web bundles (no `web/dist/`)

### Node Benchmark Workspace

- Source of truth: `tools/codegen-bench/`
- Purpose: TypeScript/JavaScript codegen benchmark suite
- Invoked by CLI via `gamma.py codegen language`
- Kept out of `src/` to preserve Python/Node boundary

## Shared Infrastructure Contract

- Vendored dependency: `gamma-core/src`
- GAMMA adapter: `src/core/gamma_core_adapter.py`
- Optional override env var: `GAMMA_CORE_SRC_PATH` (absolute path to `gamma-core/src`)

## Training / Distillation Pipelines

- Location: `projects/distillation/`
- Embedding track: `projects/distillation/embedding/`
- Translation track: `projects/distillation/translation/`

## Supporting Surfaces

- `tests/` regression + docs-parity checks
- `tools/` utility scripts and external benchmark workspaces
- `mcp-server/` MCP integration surface
- `docs/` operator/developer documentation

