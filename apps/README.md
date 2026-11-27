# Applications

| Application | Entry point | Local checks |
| --- | --- | --- |
| Mandate 2038 | [mandate-2038/](mandate-2038/README.md) | Its `AGENTS.md` and `package.json` own deterministic builds/tests and publication gates. |
| Browser token game | `web/index.html` | Static ES modules; serve `web/` directly. |
| Gamma MCP server | `mcp-server/server.py` | Python MCP adapter importing the Gamma toolkit. |
| Flux | `flux/flux.py` | Independently packaged diffusion lab; its `src` package is separate from Gamma's `gamma` package. |

Each application keeps its own dependencies and build surface. [Gamma](../gamma/)
owns the model toolkit. [Gamma Core](../gamma-core/README.md) provides shared
primitives and has its own package metadata. Flux accepts `GAMMA_CORE_SRC_PATH`
for an explicit Gamma Core source checkout.

To verify installed Python app boundaries without fetching dependencies, run
`python3 -m unittest discover -s apps/tests -p test_installed_wheels.py`. It uses
available setuptools/wheel and an isolated environment; actual MCP stdio coverage
requires the already-installed MCP SDK. It performs no model execution.
