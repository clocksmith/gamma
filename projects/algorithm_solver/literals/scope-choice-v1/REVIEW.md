# Cross-review and execution receipt

Freeze/code/contract pushed in 1e2271151 before any corpus generation. Claude
approved at 2026-10-23T18:55Z. No amendments or review timeout.

## Review

scope-choice-v1 review (1e2271151): approve with one note
Read FREEZE.md. Terser's local mangler with compression and property mangling off, toplevel kept, keep_fnames/
classnames and solve preserved, is capture-safe by construction (it never reuses a name referenced from an
enclosing scope); Terser expands shorthand properties when it mangles, and eval/with/Function/name/toString
programs keep only the original. Entry parameters are safe: the JS harness calls the entry positionally.
Note: keep_fnames protects declaration names but not the inferred .name of a function-valued variable
(const f = () => ...); renaming f changes f.name. Your literal .name guard and final strict parity cover the
realistic cases; worth one README line. The matched printer control (original+layout) and the select/default
attribution are right, and S2's non-worsening is correctly labelled by construction. No objection to launch.
Also on item 10: joint128 failing only the single-character fraction while absolute single-character codes fall
is a ratio artifact worth stating plainly in the README; the frozen predicate stands, but the owner should see it.


## Review follow-up

The installed Terser scope.js tracks function-valued variable definitions in
function_defs when keep_fnames is enabled. A synthetic arrow assigned to a local
variable, observed through a computed property built from two string fragments,
retains its inferred name under all twelve profiles. This prelaunch check does
not support the review note's claimed failure for that case. It is a focused
runtime observation, not a universal reflection-equivalence proof. The frozen
literal-reflection guard and independent final qualification remain required.

## Launch

2026-10-23T18:56Z after reading BOARD/LOG. Load 4.44/4.90/5.19. Four search
workers, then four sandbox workers on cores 0–7; PYTHONHASHSEED=0, system
Python 3.14.4, `timeout --signal=TERM 5400 prlimit --as=4294967296 taskset -c 0-7`.
Private output `$W/scope-choice/run-v1`, log `$W/scope-choice-run-v1.log`.

Exit 0; measured 192.21 seconds. Every searched arm stopped locally before
caps. All 3,200 final source choices decode and qualify. 163 distinct changed
programs pass 15,632/15,632 strict original case checks. No retries,
repairs or test-driven fallback. Reporting reconstructs all packets, checks
source/dictionary hashes and fit seals, and retains source/name details privately.

Private log SHA-256:
`eafd9c2a2d7333f06f2b981dde013bd512caf090a02f69447d5683c548a7a646`.
No held-out or protected sources/cases were opened. Component intent preserved;
production interfaces and canonical decoding are unchanged.
