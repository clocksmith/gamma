# Vocabulary-aware local syntax alternatives

Board23, goal2b. Item13 changes bound names; item10 chooses among complete compiler
outputs. Test a different bounded source search: choose individual equivalent
syntax spellings by exact literal cost, preserving variable names and algorithms.
This complements those prior mechanisms; it is not a general optimizer, new
representation or novelty claim. Item15 runs independently on separate cores.

## Sources, arms and fixed policies

Start from item13's selected scope_joint256 dictionary and fit sources. Retain
originalR and the seed among all source alternatives, with the same300fit/
100consumed-validation allowlist and pinned case/qualification contract. The
seed was selected on development validation; all results remain adaptive
development. Final held-out100/protected66 stay closed. No corpus extraction,
cost probe or timing smoke preceded this freeze; only synthetic programs were
used to implement and check the transformation rules.

Five256-entry/eight-bit arms:

- seed: exact item13 replay;
- arithmetic: fixed dictionary, assignment/update alternatives only;
- flow: fixed dictionary, branch/loop alternatives only;
- combined: fixed dictionary, both families;
- combined_joint: both families plus ordinary dictionary refitting.

Each non-seed arm gets two fit rounds: rewrite currently selected sources, retain
all original/seed/prior variants, exactly reselect, then refit only in combined_joint.
Variant selection minimizes complete program selections, tie by byte length then
variant key. All fixed arms keep the same dictionary. A chosen transformation must
strictly lower whole-program selections; no byte-only acceptance or equal-cost
exploration. The combined family has more candidate types, explicitly extra
search opportunity under the same cap rather than identical proposal counts.

After each arm's fit dictionary and selected fit sources seal, validation chooses
originalR/seed by exact count, byte length and source text, then uses two calls of
that arm's same rewrite policy under the sealed dictionary. No validation refit.
Seed is unchanged. Fit and validation choices all seal before execution tests.
Compare combined_joint to combined to separate dictionary fitting from the
common source-search family; arithmetic/flow isolate available transformations.

## Guarded AST alternatives

Acorn2022 parses source and eslint-scope resolves identifier references. Preserve
item13's eval/Function/with and explicit name/toString reflection guards. Additional
source-observation guard rejects this/arguments/globalThis/window/global/self and
member constructor/callee/caller/eval/Function access. For edits inside a function,
its named bindings must be referenced only as direct callees; otherwise skip those
edits. Anonymous function bodies are eligible only in direct IIFEs. This blocks
implicit source coercion such as returning a function as a string, including
escaped callback bodies. Moving a branch preserves its nested function source
text. Unsupported forms remain unchanged and are reported; guards are conservative.
Finite qualification does not establish universal equivalence for arbitrary JS.

Arithmetic family:

- For a resolved non-global identifier x, expand x op= y to x=x op (y), or contract
  x=x op y when the target and read resolve to the SAME binding. Operators are
  +,-,*,/,%,**,<<,>>,>>>,&,|,^ only. No member targets, logical/nullish assignment,
  increment-to-addition conversion, commutative operand swapping or coercion
  assumption. Both forms read the old x before evaluating y, even when y rebinds x.
- Toggle prefix/postfix ++ or -- only when its value is discarded: expression
  statement, for init/update, a nonfinal sequence member, a final sequence member
  whose parent discards it, or void's argument. Used return/condition/assignment
  values are excluded. Target remains the same resolved identifier.

Flow family:

- Invert if/else only when both branches are blocks: negate its condition and swap
  the complete blocks. Invert ternary branches analogously, with explicit grouping.
  Condition evaluation still occurs once, and only the original selected branch
  runs. Negation uses !(test), or removes one existing ! with grouping.
- Spell while(test)body as for(;test;)body, and an empty-init/empty-update for as
  while(test)body (true when the test is absent). Preserve the complete body and
  enclosing labels; continue still reaches the condition. No for-loop initializer,
  update expression or lexical declaration is moved.

Reparse every proposed full program. Reject complete-source/solve-definition/body
strings that equal a dictionary entry before scoring. Do not execute candidates
during search. Names, source bytes, comments lost inside replaced syntax spans,
and all added parentheses/operators are charged through the final exact source.
No free operand, source escape, helper or semantic decoder exists.

## Search budgets, storage and qualification

Each rewrite call permits20accepted single-node moves/2000exact candidate scores;
re-enumerate after every accepted edit. At most256distinct proposals per enumeration,
sorted by source start/end, kind and replacement text. Choose lowest selections,
then byte length, then source text. Report proposal truncations, trials, accepted
kinds, stop reasons and source hashes. Local stopping does not prove global source
optimality or rule out improvements from unoffered transformations.

Combined_joint uses the shared two-owner selected-span proposer and the same
local dictionary search as item13: each round30000trials/600seconds;24refill
shortlist,96additions,500swaps,150pairs,16pair-addition/8pair-removal shortlist.
Whole-source/body strings from all retained fit variants are banned. Skip pruning
at an exhausted budget. Other arms evaluate their fixed dictionary only. Retain
all prior source variants after dictionary changes. No learned scorer or LNS.

All2000final choices independently decode to the selected source bytes. Every
distinct changed source/ID pair passes ALL pinned original cases and strict
observation parity in the existing isolated judge. UnchangedR reuses its pinned
receipt. No retries, repairs, test-driven fallback or excluded failures. Whole-body
audits also cover retained validation variants. These local syntax changes retain
algorithms/control-flow work and asymptotic complexity; cases test finite behavior.

Charge all exact literal selections, one Finish, dictionary bytes, eight-bit
payload,41-byte frames and padding. Report all fit/validation costs, median/p90/
p95/worst,<=32/96, character counts/fractions, paired changes, source bytes,
qualification, raw/decoder-source-inclusive packages and offline tooling inventory.
Full runtime installation size remains unmeasured. Private source/codebook/sequence/
trace/case data remain private. Reporting is separately rerunnable from artifacts.

## Predictions and unchanged decisions

- S1: seed reproduces item13 fit/validation selection counts.
- S2: arithmetic improves actions for at least20validation programs versus seed.
- S3: combined has fewer validation actions than either individual family.
- S4: combined_joint saves at least1%validation actions versus seed.
- S5: all2000choices decode/qualify and whole-solution audits are clean.
- S6: at least one arm passes the incremental successor rule below.

Readiness against historicalR/L-R256 remains all400qualified,100validation decoded,
clean audits,>=5%fewer validation actions, strictly lower action median/p90,
>=60better/<=25worse, nonincreasing character fraction and rawpackage<=105%.
An incremental successor must additionally beat item13 in total actions, with
median/p90/fraction nonincreasing,<=25worse and package<=105%. Rank such candidates
by actions,package,armname; report every failed predicate. Combined_joint versus
combined is a separate attribution contrast, not silently folded into the control.
No M1 qualification or independent-generalization claim from these400dev choices.

## Resources and review

Two search processes, then four sandbox workers, allcores8–11;4GiBaddress-space
per process,3600-second global cap,PYTHONHASHSEED0. No GPU/model. This runs beside
item15cores0–7 and Claude's item22cores26–31 without changing their budgets.
Four focused Python tests pass (cost-guided expansion, family ablation, exact cap,
unsupported reflection) plus127 independent synthetic behavior observations in
Node, including all compound operators, BigInt/string coercion, RHS rebinding,
valueOf order, discarded values, branch effects, labels/continue, and direct versus
escaped functions. Parse/compile/import/help checks pass. No broad test campaign.

Freeze/code/contract pushed, then Claude review or PLAN30-minute timeout before
launch. Component intent preserved; canonical codec, production behavior and M1
thresholds unchanged. Confirmation, protected opening, training, source publication,
BITS deploy and human study remain owner-gated. No ledger/catalog/claim writes.
