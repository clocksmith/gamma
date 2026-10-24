# Item44 canonical policy auxiliary

This separate, unpinned reporting component answers Claude's 2026-10-24T00:19Z
request to compare the retained seed and final item44 dictionaries under both
encoding policies. It preserves the root and algorithm-solver CATSCAN intent:
source-bound representation measurements, complete charges, separate reporting,
closed protected populations and unchanged qualification/promotion authority.
It does not modify item44 execution, its accepted primary report, or its pins.
The sibling location keeps these files outside item44's direct-child binder.

No private input was opened to implement or test this auxiliary. Root may run it
only after the primary independent report is complete and accepted. The command
requires its actual output directory, including the successful report supervisor
receipt, rather than a lone copied results file. It refuses absent, failed or
incomplete primary evidence before opening any private run/source/dictionary.
It binds the primary contract, accepted report, primary production result and
per-arm result hashes; rechecks code/runtime pins, decoder inventory, exact source
file hashes and original item13 per-source qualification hashes. This is inherited
source identity, not new execution or qualification.

Both policies use the same **stored sorted literal IDs** of each retained
item44 dictionary:

- **min-F:** minimize `(10C−N, N, complete ID sequence)`.
- **canonical min-N:** minimize `(N, complete ID sequence)`. There is no C tie
  break. This matches `literals.shortest_encode` for the same ordered dictionary.

Historical parent dictionary hashes remain separate. Sorting a parent dictionary
can change canonical ID ties and C; this report does not pretend to reproduce
canonical metrics under the parent's original ID order. N excludes Finish;
actions include one Finish per source. Both policies cover exactly the same 300
fit sources in each of R and naming, reported separately. No validation or other
population is loaded, and no dictionary/source search or selection runs.

An independent sliced-string DP reconstructs both full ID sequences. The min-F
sequence must match every retained packet byte and all primary per-program and
aggregate costs. Canonical packets are constructed and independently decoded in
memory with the same eight-bit codec. Every singleton consumes a paid dictionary
slot; no fallback exists. Report F, C, N, actions, arithmetic median, nearest-rank p90/p95 and
worst selections, action distributions, C/N, dictionary bytes, packet bytes,
framing, payload, and the exact two-file decoder inventory. Dictionary and decoder
charges are included once per corpus package and in every one-program package.
Source UTF-8 bytes are a separate diagnostic, not a hidden compressed channel.

Report signed canonical-minus-min-F and final-minus-seed changes under each
policy. Lower min-F may buy extra selections; it does not establish lower
canonical fraction. The synthetic regression has seed `[a, aaaaa]` and final
`[a, aa, aaaaa]` on invented `aaaaaa`: final min-F uses three `aa` entries with
C=0, while canonical min-N uses `a, aaaaa` with C=1 and N=2. Canonical C/N remains
unchanged despite the strict min-F gain. A separate ID-tie regression rejects
silently replacing canonical min-N by min-N/min-C.

The auxiliary is metadata-only: source strings, literal entries and ID sequences
are not published. It produces no M1 candidate, readiness test, semantic-reuse
qualification, new bound or optimization verdict. Bans/capacity/pool legality are
inherited from the accepted primary replay and unchanged dictionary hashes;
this auxiliary independently rechecks coverage and the two encoding costs.

## Bounded invocation after accepted primary replay

```sh
/home/x/deco/gamma/.venv_rocm/bin/python -B \
  projects/algorithm_solver/literals/direct-fraction-exchange-report-v1/canonical_shadow.py \
  --work <private-work-root> --run <accepted-primary-production-directory> \
  --primary-report <accepted-primary-report-directory> \
  --output <fresh-separate-auxiliary-directory>
```

One process, affinity cores6/7, 8 GiB address space, and a 1200-second hard
`BaseException` alarm cover setup through final publication. No subprocesses or
solvers are launched. Root schedules execution after the primary replay has
released those cores. Overlapping primary input/output paths are rejected without
writing to them. Refused reuse of an auxiliary directory or any later error
withdraws auxiliary success and writes no-verdict metadata, even if writing a
failure receipt itself fails. The primary files are always read-only. Success
publication stages both files and replaces complete JSON last. The output records
all three auxiliary file hashes separately from the frozen execution contract.

## Focused development checks

`test_canonical_shadow.py` uses invented inputs only: exhaustive tiny segmentations
and legacy canonical equivalence, full two-cohort300-row replay with exact codec
charges and policy divergence, corrupted retained packet rejection, accepted
primary gate ordering, active setup deadline, and failure-receipt/publication
withdrawal. These checks do not establish corpus performance or qualification.
