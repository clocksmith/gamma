# Cross-review and execution receipt

Freeze/code/contract pushed in c306b899f. Launch HEAD07c0aea07 adds dated
reporting metadata notes only; frozen code hashes match. Claude approved at
2026-10-23T19:15Z. No run amendment or review timeout.

## Review

binding-descent-v1 review (c306b899f): approve
Read FREEZE.md. The constraint set is the standard sufficient condition for capture-free per-binding renaming:
same-scope distinctness; for every resolved reference to u, no other binding on the path from the reference's
scope up to u's scope may share u's name (no new shadowing, and no lost shadowing since topology is fixed); no
eligible binding takes an unresolved spelling visible from its scope; fixed/alias vertices never edited. var
hoisting, parameter/default scopes and function-expression name scopes come out of eslint-scope resolution, so
they are covered by the reference-path rule; targets a-z exclude arguments; eval/with/reflection programs are
retained. Keeping function-valued variables fixed also avoids the inferred .name issue I raised on item 12.
Matched contrasts are labelled correctly (global vs scope under a fixed dictionary; joint arms as whole
searches). No objection to launch on cores 0-7; my item 11 run holds 28-31 until about 20:40Z.


## Execution

Actual launch clock: 2026-10-23T19:15:36Z; the shared log/board launch entry
rounded this to19:16Z. Host load5.21/5.10/5.00. Four search workers, then four
sandbox workers oncores0–7. System Python3.14.4, PYTHONHASHSEED=0,
`timeout --signal=TERM 7200 prlimit --as=4294967296 taskset -c 0-7`.
Claude's LNS widths occupied28–31 and were not touched.

Exit0; total measured242.14seconds. All dictionary searches stop
locally before caps. All4,000 final source choices independently decode and
qualify. 649distinct changed programs pass62,521/62,521checks.
No retry, repair or test-driven fallback. Reporting reconstructs each packet,
checks source/dictionary hashes and fit seals, and retains private mappings/traces.

Twelve focused synthetic tests pass, including100 independently executed legal
colorings, lexical capture/unresolved-name cases, fixed aliases/inferred names,
recursive globals and retained budget incumbents. Compilation/import/help pass.
The unchanged judge/lane infrastructure retains A's37 checks.

Private output: `$W/binding-descent/run-v1`; private log SHA-256:
`fe993c0e6aa7658792062fd0d322a12d91d595806a2bec02a549ef084b059ee1`.

Both scope256 andscope_joint256 pass development readiness; frozen ranking
selects scope_joint256. Confirmation stays at the owner gate, with no held-out
or protected opening, source publication, BITS change or M1 claim. Component
intent preserved; canonical decoding and production interfaces unchanged.
