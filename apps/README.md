# Applications

| Application | Entry point | Local checks |
| --- | --- | --- |
| Mandate 2038 | `games/2038/` | Its `AGENTS.md` and `package.json` own deterministic builds/tests and publication gates. |
| Browser token game | `web/index.html` | Static ES modules; serve `web/` directly. |
| Gamma MCP server | `mcp-server/server.py` | Python MCP adapter importing the Gamma toolkit. |
| Flux | `flux/flux.py` | Independently packaged diffusion lab; its `src` package is separate from Gamma's `gamma` package. |

Each application keeps its own dependencies and build surface. Shared Gamma
runtime code stays at the repository root; gamma-core is an adjacent checkout or
installed dependency. Flux accepts `GAMMA_CORE_SRC_PATH` for an explicit checkout.
