# Item 38 prelaunch freeze draft

**DRAFT: not execution-frozen or authorized to launch.** Root must obtain Claude's review, settle changes, regenerate pins and activate the executable contract before private source/case access or execution. No existing frozen item changes.

The contract is [DRAFT.md](DRAFT.md), pinned implementation and pending-contract.json. Approval/activation freezes those exact choices in contract.json. No data-dependent amendment after launch.

## Fixed experiment

1. Exact item31 own-width128/256 scope_joint anchors;27 fit/9 consumed validation. Closed14/all50/final100/protected66 forbidden. Parent contract/qualification and opaque anchor-file hashes come from public manifests only. Pending pin generation reads no private inputs; authorized use checks exact hashes.
2. Eight arms U/S/D/J ×7/8-bit widths and two R references. U fixed source/dictionary; S menu/fixed dictionary; D fixed source/two rounds; J menu/two rounds. No cross-width selection.
3. At most six standard-library renderings, original retained, identical location-free AST including type comments, exact literal/formatted-string spans, printable-ASCII/LF changes and conservative observability guards. Unsupported original-only. Exact guard list is in render.py/DRAFT.md.
4. Source choice: canonical N, packet bytes, source bytes, unchanged-on-exact-tie, lexical source. D/J:2×60 seconds and12,000 trials per round; neighborhoods96 additions/500 swaps/150 pairs/16 pair additions/8 removals/.25 designed fraction. All96 fallbacks. No extra round/retry/qualification-guided choice/fallback.
5. New proposals exclude all fit-menu full sources/method bodies. Audit full actual dictionary including inherited seed against all fit+validation menus. Any collision is a hash-only legality failure. No exemption, pruning or post-outcome variant dropping.
6. All eight fit seals before validation-source parse; all choices/R references before cases. Distinct new sources qualify once per(ID,hash), shared across arms. Exact unchanged31 sources reuse pinned passing receipts. Failed selected sources stay failed.
7. Independent replay verifies288 experimental+72 R views: metadata/source binding, menus/AST/literals, arm constructors, choices, codec, seals, bans, fresh observations and costs. No optimization/execution in replay. Incomplete execution/artifact mismatch gives no verdict. Qualification/legality failure gives no eligible-candidate claim; missing coverage retains denominator and nulls full-cohort totals.

## Resource bounds and failure

Eight fit workers, one per arm, cores0–7 in width then U/S/D/J order,8GiB each,300-second worker alarm including menus/setup and two60-second rounds. Eight validation workers use the same disjoint cores,8GiB/180 seconds, only after fit pool exits. R reference encoding is serial under the overall deadline.

The reused search clock is checked at operation boundaries; an in-flight exact evaluation can cross the60-second search budget. The300-second worker alarm and2400-second overall deadline are hard bounds. Report actual round durations and trial counts rather than claiming exact equal compute.

Timing receipts must be finite, numeric and nonnegative. The frozen receipt tolerance is1 second for recording/scheduling overhead; it does not extend any execution alarm. Fit receipts are bounded by300 seconds plus tolerance and by the runner; search-round sums by their fit receipt plus tolerance. Runner/final-status receipts are bounded by2400 seconds plus tolerance and ordered within the enclosing supervisor; supervisor receipt is bounded by2400+30 cleanup seconds plus tolerance. Qualification batch wall time includes sandbox setup/reaping and up to two5-second reader joins plus a1-second writer join, so it is not equated to the8-second payload timeout. Each batch and each deterministic worker's sum of batch walls must fit the1800-second qualification/overall-run enclosing bound plus tolerance. NaN/infinity, negative, incoherent or over-budget receipts produce no verdict.

Qualification follows both pools: four workers, disjoint deterministic key lists, cores0–3,8GiB and1800-second worker phase deadline. Each source is attempted once in32-case batches with3 CPU/8 wall seconds,512MiB sandbox memory and4MiB output. Failures are recorded; subsequent declared batches continue without rerun. At most144 distinct new sources. Exact new-source/case counts seal before execution.

Runner deadline2400 seconds; supervisor allows30 seconds cleanup and kills its process group. Sandboxes retain existing die-with-parent isolation. Threads fixed1; no other cores/GPU/model/download/network. Independent reporter is separately core0,8GiB/600 seconds; replay cost is separate from search/qualification.

Timeout/OOM/partial seal/missing artifact/preflight failure is retained, with no retry/resume or incomplete-cohort promotion. Existing output directories are refused. Assertions remain enabled; any PYTHONOPTIMIZE setting fails closed.

## Predictions and pass rules

Directional guesses fixed before source access; no invented probability:

- P1: All288 experimental+72 R views decode and qualify, with zero illegal entries.
- P2: At least one width has S validation actions strictly below U.
- P3: At least one width has J validation actions strictly below D.
- P4: At least one width has J validation actions strictly below S.
- P5: No rendering arm passes all strong and incremental readiness gates.

P2–P4 require both compared full cohorts to decode/qualify/be legal; signs on invalid candidates do not satisfy them. Every prediction is reported.

S/J readiness: strong gates versus R and D, incremental versus U; J additionally incremental versus S. Strong: both36 qualified/covered, legal/within width;≥5% fewer validation actions, lower median/p90,≥6 better/≤2 worse, nonhigher character fraction and≤105% package. Incremental: strict action reduction, nonhigher median/p90/fraction,≤2 worse,≤105% package, same full-cohort gates. No threshold/subset/best-width/partial-cohort changes. U/D are controls.

Costs charge global dictionary, headers/padding/Finish, decoder source, source bytes, offline inventory and measured fitting/runner costs. Per-split full-cohort availability is explicit; partial encoded-row descriptive costs stay labeled with full-cohort totals null. Model/training costs zero; installed runtime unmeasured. M1/M2 remain unchanged.

## Review and activation

Development: `python3 -m unittest test_render test_engine test_pipeline test_contract` plus syntax/import checks. `python3 make_contract.py` refreshes pending public pins with no private read; output is non-executable.

Only after root/Claude approve: `python3 make_contract.py --activate`, inspect digest, then `python3 launch.py --output <fresh-private-run-directory>`. After supervisor completion, `python3 report.py --run <same-private-run-directory>` writes metadata-only evidence/REPORT.md. Root owns approval record, actual location, execution and publication/commit/push. These launch commands must not execute during draft development.

Preactivation review amendment, 2026-10-23: activation requires exact current-versus-reviewed pending equality, verifies every pinned code/runtime/public-input byte, then copies the reviewed payload changing only execution_authorized=false to true. Drift requires a refreshed draft and review, never silent repinning at activation. Resolved Python, ast.py and tokenize.py are explicitly pinned. Report input top-level keys are exact; search-stop values are fixed_dictionary, trial_limit, time_limit or local_optimum with arm-specific restrictions, and copied numerical fields are validated. A failed replay overwrites any stale successful REPORT.md with explicit no-verdict text as well as failed metadata. No activation or private input access has occurred.
