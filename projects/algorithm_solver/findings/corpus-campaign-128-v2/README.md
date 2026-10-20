# Bilingual corpus campaign: 33 reviewed problem pairs

The later [51-pair checkpoint](../corpus-campaign-128-v3/README.md) records continued work and explicit public-order admission.

This immutable revision-246 checkpoint records 66 accepted implementations across
33 problems. Each language passed 3,097 unchanged independent cases and 75 public
cases: 3,172 per language, 6,344 selected executions total. Source, contract,
structural-check, sandbox execution and independent-review artifacts were checked
against 1,889 recorded hashes. These are normalized reference results, not new
autonomous solving or semantic-generalization results. No catalog promotion is
implied. Original sources and unsuccessful attempts are preserved.

The campaign still has 4,614 pending implementations, 24 claimed for current work,
and four blocked entries (both languages for 599 and 633). The 2,354-problem
eligible population, 618-item separate qualification backlog and 381 frozen
boundary entries retain their definitions from the
[first accounting report](../corpus-campaign-128-v1/README.md).

599 passes 95/96 strict cases; the statement allows any output order, and the
approved original fails the identical example tie-order comparison. The existing
statement-bound public comparator will be evaluated under a separately versioned
contract. Its historic strict failure is not waived. 633 passes 47/54 existing
cases and all 43 official-domain cases. Existing extra-domain integers exceed the
exact JavaScript Number range; a separate integer transport and algorithm profile
would be required. Full-set acceptance remains blocked.

Accepted IDs: 121, 136, 148, 153, 169, 242, 252, 253, 300, 347, 387, 526, 532,
537, 539, 541, 542, 544, 547, 551, 553, 566, 575, 581, 582, 583, 594, 605, 611,
625, 643, 645, 647. See `summary.json` for per-language hashes and case counts.

The frozen private ledger and content-addressed artifacts are under
`runs/corpus-campaign-128-v2/`; original batch packages remain separately named.
The live single-writer ledger remains
`/home/x/Documents/Codex/2026-10-19/task/corpus-campaign-v1/ledger.json`.
Run the `next_command` in `summary.json` to inspect current progress. Continue
pending batches and resolve explicit comparison/fixture defects; do not infer
completion from this checkpoint. No public Git push or site deployment occurred.

Fleet reconciliation reverified all 150 delivered W002 sources on128, Mac and
Suby against preserved hashes. All six Mac original ZIP hashes matched. No new
B07-B10 deliveries were found in accessible preserved paths;100 assigned problems
remain unavailable. Existing helper scripts were inspected but not invoked because
rdpush also publishes to origin. See `w002-reconciliation.json`.
