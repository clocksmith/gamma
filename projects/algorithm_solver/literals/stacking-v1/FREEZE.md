# Flat stacking v1 execution contract

2026-10-23. Prelaunch review draft until committed/pushed and approved by Claude.
No corpus search, rewrite or qualification has run for this experiment. Source
intent is preserved under the algorithm_solver charter. The broader
[DRAFT.md](DRAFT.md) records the ranked evidence and a separate structured2c
proposal; **this execution contains only the eight flat outputs below**. The2c
sidecar needs its own complete code, freeze and review before execution.

## Target and population

Start at item13 scope_joint256 to measure component attribution. Compare against
originalR, item13 and current-best item24 optional (8336validation actions,
median61.5/p95197 selections,49.5993%character fraction,14998package bytes),
without editing their frozen artifacts. Item24 remains the selected default if
this run has no successor. Use only A's fit300/consumed validation100 allowlist.
No final100/protected66 loading, authoring, model/training, publication, deployment
or live-profile changes. Known-source offline optimization is not composition.

## Source factorial

N: ordinary13 a-z binding continuation; NC: add14coupled proposals;
NP: add10compiler alternatives; NCP: both additions. Two fit rounds per arm.
All use the same source-dependent v3 local dictionary algorithm and cap of
300seconds/12000trials per round. No dictionary exceeds256entries.

Each round compiles only the selected source using pinned layout/syntax/standard
Terser profiles (or retains it alone without compiler). Each of the at most
four distinct outputs undergoes ordinary naming (2sweeps/6000trials); coupled
arms additionally use3rounds/512proposals/100000states. Lexical records are rebuilt
per input and every output reparsed. OriginalR,13seed and prior selected round
sources remain candidates. At most12distinct variants per program after exact
hash deduplication. Variant IDs sort by source text, yielding source selection
by minimum literal selections, source bytes, source text. Strict improvement
rules inside the existing naming algorithms stay unchanged. Added components
add measured compute; equal caps do not imply equal work.

Keep all encountered whole-source/body strings banned across fit rounds,
including earlier unselected variants. Fit-only dictionary fitting can choose
among retained variants. Final source selections, dictionary, traces, bans and
hashes seal before validation. The selected NCP fit bytes, regardless of fit or
later validation rank, are the fixed source cohort for deeper stacking.

## Two repair trajectories and four continuation outputs

Start both trajectories from identical NCP fit sources/dictionary. Fixed96
reserves all96alphabet entries; optional reserves every character not observed
in those fit sources and may free observed character entries. Four repairs,
120solver seconds each,600seconds per trajectory including model building.
Free48entries total, optional up8characters (up4lowest current canonical-use
priority, remaining random); learned candidates are shared fit2–64strings,
top3000 plus1000random and freed incumbent entries. Seed2800, common policies
except the declared character freedom. No implicit character arcs.

Use26's pinned directHiGHS model, threads1, algebraically verified full incumbent
start for BOTH conditions. Preserve every solver status and exact returned cost;
accept only strict minimum-N fit improvements. The warm start is robustness,
not a claim of prior search gain:26's retained incumbents tied8/8. No22relative
or nonregression objective and no27palette component is imported.

Fork each trajectory's final dictionary, without rerunning repairs:
D00=fixed96+4N objective; D01=same repair snapshot+4N+C;
D10=optional+4N; D11=same optional snapshot+4N+C.
Each finishing search has300seconds/30000trials, common neighborhood, source
bytes fixed. Coverage-safe code preserves only actually supplied characters,
counts infeasible proposals and rejects them. It does not use18's ordering
helper that restores all96characters. Fixed96characters or optional fit-unseen
characters remain reserved. Optional observed missing characters can return
only as paid selected entries. Deletion-only infeasibility does not logically
exclude a coverage-restoring swap, but the bounded shortlist may screen such
swaps out; no global/local-exhaustiveness claim follows. Final objectives can
trade extraN for fewerC; all actual costs remain charged.

## Validation, encoding and qualification

All eight fit dictionaries seal before any new validation source selection.
N/NC/NP/NCP apply the same two source-proposal rounds to original/seed validation
sources under their own fixed dictionary, without refitting. All fourD arms
reuse the identical final NCP validation bytes; no adaptation to theD dictionary.
Missing validation coverage fails; no implicit escape, retry or source fallback.

Every output/reference gets canonical and shortest_min_char (minN/minC) packets.
Primary selection uses shortest_min_char for BOTH candidate and every comparator;
canonical remains a complete matched shadow and cannot retrospectively change
13/24 records. Decode independently with the unchanged flat codec. Each output
pays every8-bit selection, one Finish,41-byte header, padding and full dictionary.
Report source bytes, entry counts, character counts and fraction, selection and
action quantiles, per-program/amortized packages, decoder-source and offline
compiler/solver tooling separately. Full installed runtime storage is unmeasured.

Seal all source choices before running any cases. Deduplicate identical
problem/source hashes. Only exact13R and15seed hashes reuse those pinned
qualification receipts; every new final source runs all original cases and
strict observation parity under unchanged sandbox limits. Four sandbox workers.
Persist all failures independently of subsequent completions; no retries,
replacement or test-driven repairs. Historical23 unchanged-source1079exit137
remains recorded. Reuse is not a new passing execution. Failed outputs remain
in every denominator and block readiness.

## Promotion and predictions

For each policy separately, require all400fit/validation encodable and qualified,
<=256entries and clean whole-source/body audit. Existing readiness versus matchedR:
>=5%fewer actions, strictly lower median/p90, >=60better, <=25worse,
nonincreasing character fraction and raw package<=105%.

Additionally require strict lower validation actions versus EACH of13,current24
and N, with median/p90/fraction nonincrease,<=25worse and package<=105%.
D outputs must also pass those incremental checks against NCP; D01 andD11 must
also beat their matched same-repair w0output. Thus a source improvement cannot
hide a regressive added component. Rank eligible primary-policy outputs by
actions, raw package, character fraction, declared orderN/NC/NP/NCP/D00/D01/D10/D11.
No eligible successor means retain item24 canonical, not item13. Report matched
canonical-policy decisions too; never mix policies to obtain a pass.

Predictions fixed before launch, scored as true/false without changing rules:

1. S1: all reference canonical counts reproduce and every stored packet replays.
2. S2: NC uses fewer validation actions than N under matched minN/minC.
3. S3: NCP uses fewer validation actions than NC.
4. S4: D10 uses fewer validation actions than D00 with complete coverage.
5. S5: at least one w1output lowers absoluteC without more actions than itsw0pair.
6. S6: a new flat output passes every successor check against current24.

No prediction is already an achievement. M1 remains400/500,<=256entries,
median<=32,p95<=96selections,<=10%character-selection bits,zero whole-solution
entries. This400development run cannot qualify it. Item25's fixed-source and
pool-restricted certificates remain valid; source changes/new pools alter their
premises, not the10%gate. No universal impossibility or independent confirmation.

## Runtime and prelaunch checks

Pinned SciPy Python, CPU only; OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1.
Four source/finishing workers on0–1/2–3/4–5/6–7; two repair workers on0–3/4–7,
HiGHS threads1. Maximum4search processes,8GiB address-space per process,
whole execution supervisor wall guard3600seconds, followed by process-group
kill and a durable supervisor/failure receipt. Atomic phase and qualification
receipts retain partial work; a zero-new-source run still writes an empty
qualification receipt. Validation seals bind selected sources, variants and bans. No use
of Claude's8–15cores. Supervisor timeout is a resource cap, not an ETA; incomplete
arms stay incomplete and cannot be promoted. Do not relaunch a timed-out run
under the same identity. Reporting is separate and rerunnable.

Required checks: optional-character exhaustive toy paths/coverage and paid
replacement, source factorial synthetic parse/retention, promotion tests,
compilation/import/help and code/runtime/private identity verification. No
population optimization or source qualification before review. Contract hashes
pin code, allowed data, runtime and previous receipts. Reports contain metadata
only; names, source, dictionaries, packets, traces and cases remain private.
