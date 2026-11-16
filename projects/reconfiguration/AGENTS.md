# Request-specific reconfiguration

Follow [Gamma's instructions](../../AGENTS.md); [README.md](README.md) lists CPU
controls. Keep named mechanisms, versions and frozen source closures separate.
Python and Node entrypoints have different runtime/import needs; `pyproject.toml`
is a test frontdoor, not a portable model distribution. Preserve sibling WGSL and
declared toolkit dependencies. Leave active untracked query-SwiGLU work untouched.
