# CATSCAN: Gamma MCP server

Parent: [Gamma](../CATSCAN.md)

## Target

Expose explicitly supported Gamma capabilities through a bounded, installable MCP server interface.

## Authority

- Owns MCP tool/resource definitions, request validation, server packaging, and transport behavior.
- Does not broaden underlying Gamma capabilities or expose research state by default.

## Scope

- Applies to MCP tool/resource definitions, request validation, server packaging, and transport behavior.

## Contracts

- Input: Valid MCP requests and package configuration from [`pyproject.toml`](pyproject.toml).
- Output: Typed MCP responses, explicit errors, and documented server behavior.

## Invariants

- Exposed operations are allowlisted and validate inputs.
- Errors and unavailable dependencies remain explicit.
- Server transport does not alter the semantics of the called Gamma capability.

## Acceptance

- The server builds from declared metadata and its documented interface matches implementation.
- Evidence: [package metadata](pyproject.toml) and [server documentation](README.md).

## Non-goals

- Making every repository script remotely callable.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
