# Short-record decision test: draft pre-registration

**Status: DRAFT, not frozen.** It binds once the candidate's author names a frozen commit and the hash of this
file is recorded beside it (see "Order of events"). Nothing is scored before that.

## The question

Does the BITS candidate store many short records, each fetched on its own, in fewer total bytes than the best
standard method, without slower lookups?

This is the only regime where BITS has come out smallest so far
(`../rung2-short-ra-bench-v1/results/ra_pareto_benchmark_v1.json`: two suites of 160 held-out records of about
150 bytes). Those held-out sets were later used while designing follow-on variants, and the zstd baseline there
stored a full frame per record, so that result is a lead, not a finding. On the longer-record suites in the same
file tuned zstd is smaller.

## Two runs, two different jobs

- **The rerun on the old suites** (`../fair-baselines-v1/`) can only say whether zstd's per-record framing
  explained the old win. Its held-out records were already used for design. It settles nothing about the claim.
- **The run on fresh data**, described here, is the only one that can settle the claim.

## Parties

| Party | Does | May see |
| --- | --- | --- |
| Freeze owner | Pins everything listed under "What the freeze owner pins", in one commit, before the test sets are opened. | The repository and the training and validation records. Never the test records or the test source list. |
| Custodian | Built the corpora, holds the test sets, opens them only after the freeze commit, runs the scoring exactly as pinned. Has written no BITS code. | Everything. Changes nothing that was pinned. |
| Baseline author | Wrote the baseline harness without reading the BITS encoder. | The repository. Not the test records. |

The freeze owner is neither the codec's author nor the custodian. It is named in the freeze commit.

**How the test sets are kept from the freeze owner.** Before the freeze owner starts, the test records, the test
source list and the split salt are encrypted, and the plain copies are deleted. The key is held by the custodian
and is not in any place the freeze owner is pointed to. The freeze owner's instructions exclude the custody
directory. The public manifest carries the SHA-256 of each test file, so the opened files can be checked against
what was committed.

**The limit of that.** All parties run under one operator account on one machine. The encryption stops an
accidental read; it does not stop a deliberate one. Until someone outside repeats the test, every result from it
is labelled a development evaluation.

## Data

Two workloads from `../fresh-short-records-v1/`, with a third held as a spare. Each is split by source project or
collection, never by record, so no test record sits next to a training record from the same source. The public
manifest gives the training and validation sources and, for the test sets, only counts and hashes.

The spare replaces a workload only for a defect found before scoring and unrelated to any codec result: fewer than
2,000 test records, a source found in two splits, or records that cannot be rebuilt from the pinned commits.

## What the freeze owner pins

One commit, with a `FREEZE.json` in this directory, that fixes all six of these. Every choice in it is made on
training and validation records only.

1. **The codec.** The format version, the encoder and the decoder, by file hash. The candidate is the lane's own
   codec as published in this repository, not a new variant.
2. **The training recipe.** How the dictionary and code tables are built, and the dictionary budget.
3. **The seed.** One seed, or one rule for choosing it that uses validation records only. Every seed tried is
   listed.
4. **The baseline settings.** For each baseline below, the tuned level, dictionary size and dictionary kind, per
   workload, and the hash of the harness that runs them:
   - uncompressed records with an index;
   - zstd per record with a trained dictionary and the leanest framing that still lets one record be decoded
     alone;
   - raw DEFLATE per record with a preset dictionary;
   - FSST from its reference implementation;
   - small compressed blocks, reported separately, because a lookup there decodes other records too.
5. **The byte accounting.** Exactly which bytes count toward a method's total (see "Measures"), and the index form
   used for every method.
6. **The decision rule.** The gate below, with its two numbers.

Every method gets the same training records and the same chance to tune. There is one candidate. Any change after
the test sets are opened starts a new test on new data.

If the codec's author disagrees with the pinned candidate, the time to say so is before the test sets are opened.
After that the result stands for the candidate as pinned.

## Measures

- **Total bytes:** payload, framing, index and dictionary or model. Everything a reader needs to return any one
  record. Payload-only bytes are reported beside it.
- **Exact reconstruction:** every record, decoded alone, in random order. One mismatch disqualifies the method.
- **Lookup time:** median and 95th percentile per single-record lookup, in memory and warm, in one native loop on
  one quiet machine for every method. A cold first lookup, peak memory and build time are reported separately.
  An in-memory lookup is never compared with a disk read.
- **Spread:** an interval for the byte difference, from resampling the test sources.

## The gate

The numbers below were proposed in the lane's plan of 2026-11-25. They freeze with the candidate, unless a real
consumer's requirements replace them before the freeze.

**Passed** if, on both workloads:

1. candidate total bytes are at most 90% of the strongest per-record baseline's total bytes, and
2. the candidate's 95th-percentile lookup time is at most 110% of that baseline's.

The strongest per-record baseline is the one with the fewest total bytes among the baselines that return a record
without decoding any other record.

Anything else is **not passed**. There is no partial pass and no rerun with changed settings.

## What each outcome leads to

- **Passed:** put the frozen candidate into one existing storage engine and repeat the comparison with that
  engine's cache and I/O. A pass is not a product claim.
- **Not passed:** write up where this kind of codec helps and where it does not, and stop tuning on these sets.

Either way the report shows this result beside the earlier ones, including those that went against the codec.

## What this test does not say

- Nothing about longer records; there the earlier measurement already favours zstd.
- Nothing about behaviour on disk or inside a storage engine.
- Nothing about composing fragments to solve unseen problems. That is a separate question.

## Order of events

1. The custodian commits the corpus manifest (test hashes only). The baseline author's harness is committed.
2. The custodian encrypts the test sets and deletes the plain copies.
3. The freeze owner starts. It reads the repository and the training and validation records, and commits
   `FREEZE.json` with the six pinned items.
4. The custodian commits an opening record: the freeze commit, the hash of `FREEZE.json`, the hash of this file,
   and the manifest hash. Only then are the test sets decrypted and checked against the manifest.
5. The custodian runs every method on the test sets exactly as pinned and publishes the results and the test
   source list.
6. The test sets are then spent and are not used for another decision.
