# Role-canonical AST pilot

A new representation experiment, not an M1 result. See [FREEZE.md](FREEZE.md) for
the fixed 32-fit-problem population, conservative transformations and fallback
rules. No algorithm is evaluated by the AST tooling.

## Components

- `parser.mjs` checks the immutable parser receipt and all 46 upstream file hashes
  (SHA256 and Git blob SHA1) before importing explicit source-module paths.
- `bindings.mjs` adapts the previously audited binding-descent capture graph with
  deterministic syntactic roles. It does not use dictionary costs.
- `canonicalize.mjs` accepts JSON `{sources: {id: source}, mode: "role"|"format"}`
  on stdin and emits per-source transformed bytes or retained fail-closed errors.
  It checks authorized AST edits, capture invariants and post-printer AST equality.
- `qualify.py` takes the pretransformation frozen pilot manifest and exact driver
  output, then runs all 32 sources through the original typed/exact harness and
  original host oracle plus full historical observations. Failed transformations
  use reference bytes and remain in the denominator. This command must run only
  in the approved native dot sandbox execution environment.
- `verify.py` regenerates the AST outputs independently from frozen references and
  replays every retained execution observation before exposing eligible IDs.
  `--parser-node` runs only trusted parser code, never submitted source.

The original matched source and all transformed bytes are fully charged in later
literal accounting; AST metadata is not a decoding mechanism or hidden macro.
Qualification pass counts include explicitly marked reference fallbacks, not just
successfully transformed sources. `fit.py` implements the separate matched 12-arm search in
[FITTER_FREEZE.md](FITTER_FREEZE.md); it requires independently verified
exact-byte qualification before its own freeze and any fitting.

## Completed pilot: no M1 claim

Both arms passed all 2,826 frozen cases for all 32 problems, independently
verified from 106 sandbox executions each. No reference fallback was necessary.
See `qualification-summary.json` and the bounded reflection caveats in `AUDIT.md`.

All 12 matched dictionary arms completed, with independent exact packet decoding.
At 256 entries, fresh reference source scored median 129.5, p95 639 and 56.46%
character bits. Fresh role-normalized source scored median 128, p95 373 and
38.54% character bits. Inherited reference scored median 91, p95 989 and 68.91%.
Fresh initialization and common naming help reuse, but no arm meets the gates.
These numbers describe only this deliberately difficult 32-fit-problem pilot,
not all 400 development problems or the unchanged 500-problem M1 population.

`results-summary.json` retains all seed and optimized aggregate profiles and
evidence hashes. Exact private sources, dictionaries, packets and traces remain
outside the repository. The next mechanism needs structurally different
same-language algorithms and shared control-flow fragments, not a claim that
formatting alone solves composition.

## Pinned parser provenance

The official upstream source receipt is stored outside the repository at
`/workspace/shared/gamma-parser-source/receipt.json`, SHA256
`dd550ff8cb1966e56c0b2fc4a56e376d4f71ceb3175222300eb6ccfc71766365`.
The explicit source entries use Acorn 8.15.0, eslint-scope package 8.0.2,
esrecurse 4.3.0, estraverse 5.3.0, and astring 1.9.0, each at an immutable upstream
commit recorded in that receipt. eslint-scope's source exports the marker `main`;
this is not misrepresented as a generated release build. Licenses are retained.
No build/lifecycle scripts run, no upstream bytes are patched, and no absent
`dist` files are invented. `GAMMA_PARSER_ROOT` can locate an identical verified
copy, not replace the pinned dependency identities.

## Checks

`test_canonicalize.mjs` exercises capture, reserved globals, shadowing, shorthand,
inferred function names, reflection rejection, labels, destructuring, bigint,
regex, templates, directives, infinities and signed zero without evaluating them.
`test_role_qualification.py` uses only synthetic sources to check fixed population, explicit
fallback, mode mismatch rejection and exact-integer/bool transport.

Private source strings, raw AST audit outputs and frozen cases stay outside the
repository. The final held-out 100 and protected 66 remain unopened.
