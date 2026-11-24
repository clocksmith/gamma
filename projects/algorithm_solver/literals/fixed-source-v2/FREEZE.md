# Fixed-source vocabulary retest v2: frozen design

Run ID: `fixed-source-v2-r1`. Written before any v2 dictionary was mined. Only
synthetic fixtures and the census below have run. It implements the
[v2 protocol](../FIXED_SOURCE_PROTOCOL_V2.md). The owner approved the retest on
2026-11-23.

**Question.** On the same source bytes and budgets, what changes when a multibyte
entry may come from only one file? This is in-sample representation. It says
nothing about unseen code, model output, solving or end-to-end compression.
[v1](../fixed-source-v1/FREEZE.md) stays unchanged and answers its own rules.

## Inputs

The [v1 manifest](../fixed-source-v1/manifest.json), SHA-256
`fc014128dbc9505867c181d242ac0bd52b048dc8b3f483098adcd943bc66556a`: 400 problems,
one Python and one JavaScript file each, 800 distinct files, 264,908 bytes. Every
file is checked against its hash before mining and at replay. Sources,
dictionaries, parses and certificates stay private and outside Git.

## Census, recorded before search

Multibyte whole-file strings that fit within each maximum length `L`:

| Corpus | Files | Bytes | Shortest file | L at most 16 | L = 32 | L = 64 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Python | 400 | 148,488 | 44 | 0 | 0 | 3 |
| JavaScript | 400 | 116,420 | 32 | 0 | 1 | 6 |
| Both | 800 | 264,908 | 32 | 0 | 1 | 9 |

Where the count is 0, the primary and isolation candidate sets are identical, so
that isolation cell collapses into the primary. The isolation policy runs only in
the five cells with a nonzero count. Each run must confirm the difference in
candidate counts equals this table.

## Policies

| Name | Role | File support | Multibyte whole file |
| --- | --- | --- | --- |
| `s1-whole` | Primary | at least 1 | allowed |
| `s1-nowhole` | Isolation control | at least 1 | excluded |
| `s2-nowhole` | Historical matched control | at least 2 | excluded |

Support counts distinct files in the dictionary's own pool: 800 for shared, the
400 of one language for a separate dictionary. An entry is a nonempty byte
substring of one file and cannot cross a file boundary. The policy applies to
every retained entry, including BPE merges and local refinement.

## Modes, budgets and score

- **Mixed:** one-byte and multibyte entries. **Characters only:** `L` = 1.
  **No-singleton:** entry lengths 2 through `L`.
- **Grid:** `K` in 64, 96, 128, 192, 256, 384, 512, 768, 1024, 2048, 4096; `L` in
  1, 2, 4, 8, 16, 32, 64; `B` in 1, 2, 4, 8, 16, 32, 64 KiB or uncapped.
- **Serialization:** one length byte plus the entry bytes. Two separate
  dictionaries also pay 4 routing bytes against the same combined caps.
- **Score:** total emissions under the shortest-path parse, compared only between
  dictionaries that spell every file. Partial coverage is reported as files
  spelled, with tokens on those files and their denominator.

## Arms and work limits

`greedy-entry`, `greedy-byte`, `freq-occ`, `freq-doc`, `bpe` (ordinary segmentation
and shortest parse of the same codebook), `cover-mixed`, `cover-nosingle`, and
`polish`, which refines greedy for 60 seconds at each `K` from 128 up, for `L` of
8 or more. The same code, objective, ties and limits apply to every policy. The
polish limit is wall time, so its round count can differ by policy and is reported.

BPE merges a repeated pair of adjacent tokens, as in v1's unrestricted arm, and
keeps it only if the merged string is eligible. That differs from v1's restricted
BPE, which counted files on the token stream, so a v1 BPE row is context only.

At most 12 workers at the lowest CPU priority, 45 minutes per chain, 12 GiB of
address space per process. A stopped chain is reported as stopped and is never a
negative result.

## Bounds

Dual certificates for `s1-whole` and `s2-nowhole` at `L` = 16, `K` in 256, 1024,
4096, on each corpus: 18 certificates. A bound is reported only after
`check_bound.py` recomputes it in exact integers under that policy. No v1
certificate counts as v2 evidence.

## Pilot and sizing rule

Before the full matrix, a pilot runs `greedy-entry` and `cover-nosingle` on both
languages at `L` = 16 under `s1-whole` and `s2-nowhole`, verifies them, and times 100
bound iterations for each policy at `K` = 256. It records search, verification and
bound time and peak memory.

The full matrix starts if every pilot process finishes within the limits above.
Bound iterations are then the smaller of 12,000 and 6,600 seconds divided by the
slowest measured seconds per iteration, the same count for all 18 certificates.
The pilot may not change a policy, endpoint, prediction or arm. If a pilot process
breaks a limit, the run stops and any change gets a new freeze and run ID.

## Gates

1. `test_small.py` passes: one-file repeats, a whole file inside another file,
   limits at and below each budget, routing bytes, singleton violations, absent
   entries, wrong bindings, a corrupted prefix, reachability against a budgeted
   dictionary, and brute force on tiny corpora for each policy.
2. `verify.py` rejects any chain with a missing or conflicting receipt, recounts
   support, and reconstructs every file at every scored prefix.
3. `check_regression.py`: the `s2-nowhole` greedy, frequency and cover chains must
   rebuild v1's chains entry for entry.
4. `check_limits.py reach` must match the closed form for `s1-whole`: at `L` = 2 a
   file is reachable when its length is even, and at larger `L` every file of at
   least 2 bytes is reachable.

## Primary endpoints

- **E1.** Both languages, `K` = 256, `L` = 16: lowest verified complete-coverage
  emissions, uncapped and at `B` = 2 and 4 KiB.
- **E2.** Both languages, `K` = 4096, `L` = 16, no-singleton: files spelled by one
  dictionary, uncapped and at `B` = 16, 32 and 64 KiB.

Each compares `s1-whole` with `s2-nowhole`. "Best" means the lowest emissions among
`greedy-entry`, `greedy-byte` and `polish` that fit the cell.

## Predictions, written first

- **R1.** At E1 uncapped, `s1-whole` is at or below `s2-nowhole`, by less than 2%.
- **R2.** At E2 uncapped, `s1-whole` spells more files than `s2-nowhole` and at least
  500 of 800.
- **R3.** At `K` = 4096, `L` = 64, both languages, uncapped, `s1-whole` uses at least
  5% fewer emissions than `s2-nowhole`.
- **R4.** Under `s1-whole`, one shared dictionary beats two separate ones at every
  `K` up to 1024 with `L` = 16 and no byte cap.
- **R5.** At `K` = 4096, `L` = 64, both languages, the best `s1-whole` dictionary
  contains at least one whole-file entry.

## Labels

**Verified construction:** a stored dictionary, every file decoded and compared
byte for byte by the separate checker. **Bound:** a stored certificate rechecked in
exact integers. **Proved optimum:** construction equals bound. A file missed at a
fixed budget is **not found**, unless it has no parse under the policy at any
budget, which is **proved unreachable**.

## Code at freeze (SHA-256)

```text
748f8ae84e0495e60cf60cbb44b261911e59b4dbd7d125d0e3cadfa56006e7ab  engine.c
918a050cb8345f01cdc350203cc8c45c5218f52dc56812084dbd441a13a24e9f  bound.c
d3c14dbb6b21c015316bd0d5a7cc39cd9e04829ea8ba3afe617c9570ac50abe3  verify.py
3f3c2136314ad42eadb9a458403afd9f589e4cf43141793103b68bad82df2f45  check_bound.py
4a6e168ca27d4549fe9ea806d12d76abb8fb3eeb71c17e14d6d5be618c6e3662  check_limits.py
d8e33433cfb2f1ecb44032e9e271ae03a6438fac28b156dae9e7d53c7904fa63  check_regression.py
e3cbbbc0b6276dc6eb92984bc3b11fc5826a9d98be9c91ef6754a7388770646d  test_small.py
64b9187021472d13bb3a4e68292931c621857b0d6dba344879212294bb7b7137  run.sh
```

Any change to these files, the corpus, a policy or an endpoint is a new freeze and
run ID. This run stays on record, including misses.
