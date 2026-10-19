# Source literal recovery: four more Goal 1a answers

A source-bound repair of corrupted imported public input literals recovered
**4/79 correct stored answers versus 0/79 control**, with zero wrong acceptances
or lost correct answers. The remaining 75 selected requests still abstain.
These four returned programs passed **438 original independent checks** and
**10 public checks**, with unchanged solution code and unchanged expected values.

| Recovered known problem | Public | Independent |
| --- | ---: | ---: |
| Decode the Slanted Ciphertext | 3/3 | 112/112 |
| Rearrange Spaces Between Words | 2/2 | 135/135 |
| Regions Cut By Slashes | 3/3 | 89/89 |
| Remove Comments | 2/2 | 102/102 |

## Exhausted dependency hypothesis

All **27 indexed stored references** across the **15 SortedList dependency
failures** still require SortedList or sortedcontainers. Most alternate source
records contain identical code. No dependency-free stored alternative exists
within this indexed set. [The inventory](dependency-alternatives.json) records
identity, source UID and code hash, without changing a reference or importing a
new dependency. This is an exhausted indexed-reference hypothesis, not proof that
no algorithm or implementation exists elsewhere.

## Implemented repair

The current parser preserves whitespace inside quoted strings, but old imported
`public_tests` still contain collapsed inputs. For example, the indexed statement
contains `"ch   ie   pr"`, while its cached public input is `"ch ie pr"`. Because
`recover()` preserves existing examples, the later parser fix did not repair
these historical imported records.

`algsolve.imported_examples.repair()` now performs a narrow offline correction:

1. Require an imported LCD record with matching source ID and split provenance.
2. Reparse every explicit public example from its statement and declared
   interface; incomplete parses or changed example counts fail closed.
3. Reproduce the historical whitespace collapse on the **literal input text,
   before parsing**. Every old test must match that reconstruction in every
   field, including expected values and comparison mode.
4. Return a new record and hashes of its original/reparsed public examples,
   statement and interface. The original imported record remains untouched.

Only public input arguments change. Expected values, comparisons, stored sources,
independent tests and budgets do not change. Reproducing the transform before
parsing matters: an escaped `\t` is not historical source-layout whitespace and
must not be silently converted into a space. A focused regression enforces this.

The experiment additionally requires the imported statement, starter, entry and
parameter list to exactly match the selected index entry. It constructs the
candidate exact query from that corrected source record. The helper is **not
called by `answer()`** and never rewrites a caller's supplied examples.

## Frozen comparison and integrity

The selection was all **79** remaining abstentions from the prior frozen
[unordered-output comparison](../known-public-order-1a-128-v1/README.md), not only
cases that looked repairable. Both arms retain that explicit output-contract
option, use the same complete 3,288-entry eligible index, and execute unchanged
selected references in the real Linux sandbox. No model or generator is used.
The comparison driver's copied module heading says “All100”; its executable
selection assertion, manifest, keys and 158 decisions all specify **79**.

All **158 public decisions were sealed before independent tests were loaded**.
Scoring uses the original independent test sets and verifies their inventory
hashes. The current implementation, index, inventory, thresholds and runtime
files are frozen in [contract.json](contract.json). The new contract omitted the
`problems.jsonl` input file; a transparent
[post-run integrity receipt](source-record-integrity.json) verifies that its
complete bytes still equal the original, preexisting library-audit frozen hash.
Per-decision correction receipts separately bind the actual statement, interface
and old/new public examples. No historical manifest was rebound or overwritten.

The resource cap was 300 seconds, two CPU threads, 6 GiB RAM and 1 GiB disk. The
runner completed in 4.286 seconds. Timings are from a contended shared host and
provide no isolated latency qualification. Raw source-bearing decisions remain
ignored under `runs/known-public-input-1a-128-v1`; report artifacts contain hashes,
counts and verdicts only.

The metadata-only census finds **seven** eligible records with this exact input
corruption. Four are the newly executed remaining gaps above. Three already
historically approved records were identified but not re-executed or requalified:
Length of Last Word, Number of Valid Words in a Sentence and Reverse Words in a
String. No protected record is constructed into a query or tested.

Software checks passed separately: the initial focused set had **50 tests and
17 subtests**; after strengthening literal-source transformation checking, all
**four repair tests and seven subtests** passed again. Changed Python files
compile and import. No judge or shared composition file changed.

## Remaining denominator and next work

The recovered catalog contains 3,353 historical entries, with 65 present protected
entries excluded and 3,288 eligible. Historical approval stays **2,456/3,288**.
The earlier parser/output-order work recovered 21 paths in development, and this
run recovers four more. That leaves **807 historical exclusions without fresh
successful paths**: 685 missing-test, 75 exact-path, 26 runtime and 21 unusable
independent-evidence entries. **2,481 is not a newly approved total.**

The next useful exact-path work is explicit public-output property validation or
source/interface binding, with adversarial checks and a separately frozen
comparison. The 685 missing independent sets require independently authored
oracles; cached flags and public examples cannot qualify them. The dependency
subset cannot advance through existing indexed alternatives, so leave it excluded
unless a separately authorized implementation or dependency proposal is chosen.
A current-runtime approval refresh must retain source/test identities and use
fresh evidence; this work does not refresh the catalog or pass the separate
18/20 recognition-release gate.

No protected scoring, training, model inference, downloads, new dependencies,
service interruption, automatic approval or public push occurred.
