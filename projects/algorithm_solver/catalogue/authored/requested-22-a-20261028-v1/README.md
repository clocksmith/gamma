# Requested-22 A: seven newly authored development pairs

Scope: authored, not qualified. IDs 726, 729, 730, 731, 732, 736 and 741, owner-requested on 2026-10-28.
Official public GraphQL responses were fetched that day to the executor and stay there. This directory keeps
only their SHA-256 hashes (raw response and `content`), the official `metaData` interfaces and summaries in the
author's own words. No statement text or official example is copied into any file here. No Git operation.

Independent reference code, domain validators, contracts, case generator and design were frozen before any
candidate file existed (`pre-source-reference-freeze.json`). References use budgeted literal atom expansion over a
recursive-descent formula tree, pairwise overlap scans, direct cover counting at interval starts, the full
subsequence set plus a separate outermost-letter interval classification, a recursive copied-scope Lisp evaluator
and enumeration of all thorn-free path pairs. No language-agreement oracle. Maximum-domain rows carry analytic
expected values.

Candidates: 726 scans right to left with a group multiplier stack. 729 keeps sorted disjoint bookings with binary
search. 731 keeps bookings plus their pairwise-disjoint double-booked overlaps. 732 uses an on-demand segment tree
over [0, 1e9) with range add and lazy maximum. 730 uses the interval DP whose equal-end case is corrected by the
nearest inner occurrences of that letter. Values stay below 2**35 with no products, so JS Number is exact. 736 is
a single iterative token scan with per-name value stacks undone at let exit. 741 moves two walkers together, with
rows r1<=r2.

729/731/732 are real native classes (`MyCalendar`, `MyCalendarTwo`, `MyCalendarThree`). Python defines them at
module scope; JavaScript exports them as properties of the callable CommonJS `solve` export, as in the native
cohort. `solve(operation_names, argument_lists)` is a separately declared trace adapter. It makes one receiver
per trace and returns null for construction followed by each `book` result. `native_harness.py/.cjs` dispatch the
original class directly with no solve fallback. `native_protocol.py` builds argument-only packets and checks
records on the host. `native-bindings.json` pins the unchanged easy16 transport and judge sandbox. The other four
IDs use canonical `solve` plus the official `Solution` method (Python) or named function export (JavaScript).

The author ran their own candidates locally after the freeze; `test_oracles.Candidates` covers all generated
and maximum cases, the official wrappers and the native classes. Results and single-sample CPU times are in
`checks.json`. That is author self-checking, not isolated or independent qualification. Official ABI, effects,
resource limits and independent result checks still require the coordinator's existing isolated runner. No
resource cap changed. Qualification status is unknown everywhere.

Statement interpretation notes: 726 group multipliers may be omitted, but the statement does not say whether an
explicit `1` may follow `)`. The validator accepts it; element counts must exceed one. 736 does not specify
leading zeros or `-0` in integer tokens; the validator accepts any `-?[0-9]+`. The 729/731/732 `metaData` also
carries generic top-level `params`/`return` (`list<boolean>`) that do not match the class methods (732's `book`
returns integer). The 729/731 constraint lines name `start`/`end` instead of `startTime`/`endTime`.

```sh
python3 test_oracles.py
python3 test_native_observer.py
node test_native_observer.cjs
```
