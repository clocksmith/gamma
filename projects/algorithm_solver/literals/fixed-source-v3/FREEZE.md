# Fixed-source comparison v3: frozen design

Run ID: `fixed-source-v3-r1`. Written before any v3 dictionary was built on the real
corpus. Only synthetic gates and a dry run on a generated corpus have run. The
[v2 results](../fixed-source-v2/RESULTS.md) were already known, so this design and its
predictions are informed by them. v1 and v2 stay unchanged.

**Question.** On the same paired Python and JavaScript programs, what is the smallest
total encoded size, counting the dictionary, and when should two languages share a
dictionary, share only its strings, or keep separate dictionaries?

This is an in-sample measurement. It makes no claim about unseen code, model quality
or a new algorithm. The certificate method used in v1 and v2 is Theorem 1 of
[Du and Chen](https://arxiv.org/abs/2609.35869), and v3 claims no method novelty.
One shared dictionary can never need more tokens than two at the same combined budget,
because their union fits that budget. Only byte-level trade-offs are open here.

## Inputs

The [v1 manifest](../fixed-source-v1/manifest.json), SHA-256
`fc014128dbc9505867c181d242ac0bd52b048dc8b3f483098adcd943bc66556a`: 400 problems, one
Python and one JavaScript file each, 264,908 bytes. Every file is checked against its
hash. Sources, dictionaries, parses and solver output stay private and outside Git.
Final held-out and protected problems stay closed.

## Primary outcome

**Total encoded bytes**, with every file reconstructed byte for byte. Each file is
parsed into the fewest tokens and written with a canonical Huffman code over the entries
plus one end-of-file symbol.

Total bytes = dictionary (one length byte plus each entry) + one code-length byte per
table symbol + payload, rounded up to whole bytes per table + 4 routing bytes when two
tables are used. Token count is secondary.

| Design | Dictionaries | Code tables |
| --- | --- | --- |
| A | one shared | one |
| B | one shared | one per language |
| C | one per language | one per language |

A storage budget `B` limits dictionary bytes, plus the 4 routing bytes for designs B and
C. A slot budget `K` limits the combined entries. Each design chooses its best verified
dictionary and split within the same `K`, `L` and `B`, sampling chain prefixes every 16
entries plus every grid boundary.

**Primary cells:** `L` in 8, 16, 32, 64; `K` in 128, 256, 512, 1024, 2048, 4096; `B` in
4, 8, 16, 32, 64 KiB or uncapped. That is 144 cells per scenario.

## Scenarios

| Name | Rule | Role |
| --- | --- | --- |
| `s1-whole` | any observed substring | Primary |
| `s2-nowhole` | in at least two files, no multibyte whole file | Control |
| `p2-nowhole` | in at least two problems, no multibyte whole file | Control |
| `s1-whole-cuts` | primary, but no piece may span a change of lexical class | Explanatory ablation |

The ablation explains where savings come from. It is not a headline and has no part in
the kill bar.

## Arms

Every arm is scored by the same shortest-path parser and byte accounting.

- `greedy-entry`, `greedy-byte`: exact marginal token reduction, analysed by Ion et al.
- `bpe`: byte pair encoding, also recorded with its own segmentation.
- `pathpiece`: our implementation of the top-down pruning in Schmidt et al. (EMNLP 2024),
  from a BPE vocabulary of up to 32,768 entries, removing the lowest-increase tenth of the
  excess over the next grid size each round.
- `freq-occ`, `freq-doc`: frequency times length minus one.
- `greedtok`: Lim et al. (NeurIPS 2025), Algorithms 1 to 3, scored by the shared parser.
- `lp-det`, `lp-bias`: Det and Bias rounding of the LP in Tempus et al. (2026), solved with
  HiGHS PDLP on both languages at `L` = 16, `K` in 256, 1024, 4096, under `s1-whole` and
  `s2-nowhole`. An LP value is reported only if the solver says optimal, and is never a
  certificate. A rounding is kept only if the final point is primal feasible to 1e-3. An
  unsolved cell is reported as unsolved.

BPE and PathPiece are not run in the cut ablation, because their merge and pruning rules
do not define a restricted parse there.

**Search floors.** A looser rule also scores the dictionaries of its stricter rules. Each
shared cell also scores the union of its best separate dictionaries when that union is
legal and fits. These floors stop search noise from creating false regressions.

## Hard time-box

CPU only on Jupiter at the lowest priority. At most 8 chain workers, 30 minutes per chain,
12 GiB of address space per engine process. At most 2 LP solves at once, 4 threads and
1 hour each, 32 GiB of address space. The chain and LP stages have 3 hours each. The whole
run has **8 wall-clock hours**. If a limit is hit, the run stops and reports what finished.
No extension without a new freeze and run ID.

## Gates

1. `test_small.py` passes on synthetic data, including policy, cut, receipt, Huffman,
   GreedTok, PathPiece and LP checks against brute force or a direct reference.
2. `verify.py` rejects a missing or conflicting receipt, recounts support, honors cuts and
   reconstructs every file at every scored prefix.
3. `check_regression.py`: the greedy and frequency chains rebuild v2 entry for entry.
4. `encoded.py` reconstructs every file it measures.

## Predictions, written first

- **V1.** Design A is smaller than C in at least 75% of feasible primary cells.
- **V2.** Design B is lowest in fewer than 25% of feasible primary cells.
- **V3.** The token-best dictionary is within 1% of the byte-best in at least 75% of
  feasible primary cells.
- **V4.** The best non-greedy baseline is within 2% of the best arm in at least 50% of
  feasible primary cells.
- **V5.** Forbidding boundary crossing raises design A's bytes by at least 3% at `K` = 1024,
  `L` = 16, uncapped.

## Kill bar

A full paper is allowed only if at least one finding holds in at least **25%** of feasible
cells under **each** of `s1-whole`, `s2-nowhole` and `p2-nowhole`:

- **K1, design inversion:** design B or C is at least 1% smaller than design A.
- **K2, objective inversion:** the token-best dictionary is at least 1% larger in total
  bytes than the byte-best dictionary.

Otherwise BITS ends with a 4-to-6-page benchmark note of the measurements, including
neutral and negative findings. Passing the bar still requires a prior-work comparison
before any novelty claim. r2 stays archived and unsubmitted.

## Code at freeze (SHA-256)

```text
7331f1eb6d7866c6b71fbb0c19be6b1f8afdfa6ff9003c95604fa9051f8db19f  engine.c
6feb429de3e4eaa39d5231ff3cdc7e3c701a14c1a636f52f8ee1e2e4bbcaae4f  verify.py
bb783cfc824c699c2e73457b466f0e679604971578028a104aa3f0eb2fb3f71b  prepare.py
d2578e68d254345e6add63da6437467b5427f0eddf44ef25d537f93381e08700  encoded.py
7e08442279918c9b0a68c2945a8c91c1b9d7720697841535f3eedd8341798b52  score.py
c2ea763aa80306770c990cc426092022402edf43ab5a3ccbd1ac88222d5d0731  solve_lp.py
2c6017d3815a490847751adb251f3b43250334cf5c8398794f2f3e2d8d8f5f6b  check_regression.py
102f88333de3f709dbbeae652f166feb9adbda00c37b964e530c3cc35a0abbdc  test_small.py
5d4508aaf8bf1494eebcb5a0904bc1c678a438b55095a93dc1c44aaefdc1fbcf  run.sh
082f1e32d92257ff1f265e1cc1edf88e598b68a736688877dae476390b5b68cd  pipeline.sh
```

Tools: gcc 15.2.0, Python 3.14.4, HiGHS 1.16.0, NumPy 2.5.5, acorn 8.16.0. Any change to
these files, the corpus, a rule, an endpoint or the kill bar is a new freeze and run ID.
This run stays on record, including misses.
