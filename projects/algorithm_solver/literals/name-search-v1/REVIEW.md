# Cross-review and execution receipt

Freeze `56e6c2dc1` was pushed before launch. Claude approved at 17:50Z on
2026-10-23 through the shared append-only LOG.

## Review

name-search-v1 review (56e6c2dc1): approve
Read FREEZE.md, bindings.cjs, rewrite.py reserved checks and the contract pins.
- Capture: spans come from eslint-scope variables (declarations + resolved references), merged by spelling and
  renamed injectively; every other Identifier in the program (including property keys and labels) is reserved, so
  a target can never collide with a key, label, global or unresolved name; globalScope.through spellings and
  shorthand values are excluded; function/class and function-valued names are preserved; eval/with/name/toString
  skip the program. Swaps between two eligible spellings keep the mapping a bijection. I see no capture path.
- optimistic:true is safe given eval/with are excluded first.
- Seal/validation: validation rewriting optimizes only the program's own selection count under the sealed
  dictionary, with no test feedback; qualification runs after all decisions are sealed and failures fail
  readiness. Fine. Please state in the README that validation programs were rewritten by the encoder, so the
  dev-val comparison is source+encoder vs fixed source.
- Charging, predictions N1-N5 and readiness are sound. No objection to launch.
On your item 5 question: I proposed item 8 on BOARD instead (Lagrangian global dictionary selection with a
pool-restricted lower bound, the "better search methods" route the owner named); FREEZE for your review soon.


## Execution

Launched after approval at 2026-10-23T17:51Z. Host load 2.74 / 3.07 / 3.04.
System Python 3.14.4, Node 22.22.1, PYTHONHASHSEED=0, four spawn search workers.
Launcher enforced `timeout --signal=TERM 7200 prlimit --as=4294967296`.
After all source/dictionary decisions, four sandbox workers qualified final
changed sources. No overlap between search and qualification worker phases.

Exit 0. All six arms completed in 138.40 seconds total. All dictionary search
rounds stopped locally before either cap. All 2,400 packets independently decode;
all 2,400 selected programs qualify, including exact-source qualification reuse.
There were 377 distinct changed sources; 37,402/37,402 case checks passed without
retry or repair. Whole-solution-entry audits are clean. Seven synthetic checks,
compilation/import and unchanged infrastructure's 37 judge/lane checks passed.

Private output `$W/name-search/run-v1`; log SHA-256 `22579a97a69017e6c1af9f0b50268a8c05d1a81cf70969985f6d5807afd01f57`.
No review timeout, design amendment, held-out opening or protected-set access.
Validation source-plus-encoder scope is explicit in the report.
