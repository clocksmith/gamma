# CATSCAN: Gamma web client

Parent: [Gamma](../CATSCAN.md)

## Target

Present Gamma's supported interactive surfaces in the browser without changing engine, game, or evidence semantics.

## Authority

- Owns browser UI composition, client state, accessibility, and web-specific integration.
- Does not own model execution truth or redefine Python-side contracts.

## Scope

- Applies to browser UI composition, client state, accessibility, and web-specific integration.

## Contracts

- Input: Supported runtime data and behavior from [web documentation](README.md).
- Output: Accessible browser interactions and visible state consistent with runtime responses.

## Invariants

- UI state never fabricates backend success or measured values.
- Browser and Python surfaces use compatible command and data meanings.
- User-visible fallback and failure remain explicit.

## Acceptance

- UI components and documented CLI/browser navigation remain aligned.
- Evidence: [UI component tests](../tests/test_ui_components.py) and [CLI parity tests](../tests/test_docs_cli_parity.py).

## Non-goals

- Reimplementing engine inference inside presentation code.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
