# Pre-registration: two capacity theorems, their tiny controls and their predictions

Committed on 2026-11-22 (UTC), before any rank, bound, optimum or coverage curve was computed on the
instances below. Every number in `predictions.json` was derived by hand. `freeze_instances.py` builds
strings and copies those numbers; it solves nothing.

The two questions are kept apart.

- **A. Witnessed saturation.** Under the witness rule, when does spelling a corpus need as many entries
  as it has characters?
- **B. Unrestricted attainability.** Under the unrestricted rule, when can a dictionary be as small as the
  rank of the programs, and when does legal parsing force more?

## Definitions

A corpus is a set of distinct strings, the programs. Its alphabet Σ is the set of characters it uses.

- **Unrestricted rule (U).** An entry is any non-empty substring of a program that is not a whole program.
- **Witness rule, threshold 2 (W2).** An entry is a single character, or a longer substring that occurs in
  at least two programs. No entry is a whole program.
- **Minimum entries.** The smallest dictionary that spells every program as a concatenation of entries.
- **Coverage at budget K.** The most programs that some dictionary of at most K entries spells.
- **Vector of a string.** One coordinate per character over the field of 1,000,000,007 elements:
  the sum of 2^i over the positions i where the string has that character.
- **Program rank.** The rank of the program vectors.
- **Forced cut, block, block rank (W2).** A boundary whose two-character window occurs in fewer than two
  programs is a forced cut. The pieces between forced cuts are blocks. Block rank is the rank of the
  block vectors.
- **Cover set of a position.** The eligible entries, as strings, that have an occurrence spanning it.
- **Forced singleton.** A character with a position whose cover set is that character alone.
- **Disjoint bound.** The largest number of positions with pairwise disjoint cover sets.
- **Cuttable prefix.** A non-empty proper prefix of a program whose vector lies in the span of all the
  program vectors.

## Claims

### Proved. A single violation means a theorem or a checker is wrong, and work stops.

- **S1.** Program rank ≤ minimum entries under U.
- **S2.** Block rank ≤ minimum entries under W2.
- **S3.** Forced singletons ≤ disjoint bound ≤ minimum entries, under either rule.
- **S4.** Minimum entries ≤ alphabet size under W2 whenever no program is a single character.
- **S5 (B, necessity).** If the minimum under U equals the program rank, every program has a cuttable
  prefix. A dictionary of that size has the programs' span, and each program starts with an entry.
- **S6.** Coverage is non-decreasing in the budget, and W2 coverage never exceeds U coverage.

### Theorem A as tested here

The disjoint bound equals the alphabet size exactly when one position per character can be chosen with no
eligible entry spanning two of them, and then the minimum equals the alphabet size. The frozen instances
test where that certificate is present, where the minimum equals the alphabet size without it, and where
the minimum is smaller.

### Conjectures. Expected to fail somewhere; the first failure is published beside the wins.

- **A\*.** On each of the 18 frozen instances, the W2 minimum equals the block rank.
- **B\*.** On each of the 18 frozen instances, the U minimum equals the program rank if and only if every
  program has a cuttable prefix. (The "only if" half is S5.)

## Instances

| Name | Programs | Why it is here |
| --- | --- | --- |
| C1 | `abc`, `abab` | permanent control: the shared piece `ab` lines up with the repeat |
| C2 | `abc`, `baba` | permanent control: same alphabet and lengths, the repeat is shifted by one |
| C3 | `ab`, `ac`, `bc` | permanent control: only single characters are eligible; rank is full |
| C4 | `ax`, `ay`, `bx`, `by` | permanent control: only single characters are eligible; one dependent set of four |
| P3a, P4a | `abc` with `ab` repeated 3 or 4 times | C1 with a longer repeat |
| P3m, P4m | `abc` with `ba` repeated 3 or 4 times | C2 with a longer repeat |
| O1, O2, O3 | hub `a`+m+`d`, with `a`+m+`e` and `f`+m+`d`; m is `b`, `bc`, `bcg` | planted motif: the two shared pieces overlap inside the hub |
| O1c, O2c, O3c | same neighbours; hub `a`+m+m+`d` | matched control: the two shared pieces abut, so they tile |
| B23, B33 | every pair from `ab`×`xyz`, `abc`×`xyz` | C4 on larger grids |
| T22 | C4 with `$` appended to every program | terminator ablation: a final character that occurs nowhere else |
| D1 | `abcd`, `abef`, `efcd`, `cdef` | four programs built from three blocks: the rank limit should be attained |

The alphabet size is held fixed within C1/C2, within each P pair and within each O pair, so only the
competing contexts change.

## Predictions

Curves list coverage at budgets 0, 1, 2, … up to the minimum.

### Unrestricted rule

| Name | Alphabet | Program rank | Forced singletons | Disjoint bound | Minimum | Coverage curve | Every program cuttable |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| C1, P3a, P4a | 3 | 2 | 0 | 2 | 2 | 0, 1, 2 | yes |
| C2, P3m, P4m | 3 | 2 | 0 | 3 | 3 | 0, 1, 1, 2 | no |
| C3 | 3 | 3 | 3 | 3 | 3 | 0, 0, 1, 3 | yes |
| C4 | 4 | 3 | 4 | 4 | 4 | 0, 0, 1, 2, 4 | no |
| O1, O2, O3 | 5, 6, 7 | 3 | 0 | 4 | 4 | 0, 0, 1, 2, 3 | no |
| O1c, O2c, O3c | 5, 6, 7 | 3 | 0 | 4 | 4 | 0, 0, 1, 2, 3 | no |
| B23 | 5 | 4 | 5 | 5 | 5 | 0, 0, 1, 2, 4, 6 | no |
| B33 | 6 | 5 | 6 | 6 | 6 | 0, 0, 1, 2, 4, 6, 9 | no |
| T22 | 5 | 3 | 0 | 4 | 4 | 0, 0, 1, 2, 4 | no |
| D1 | 6 | 3 | 0 | 3 | 3 | 0, 0, 2, 4 | yes |

### Witness rule, threshold 2

| Name | Alphabet | Forced singletons | Disjoint bound | Block rank | Minimum | Coverage curve | Minimum equals alphabet |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| C1, P3a, P4a | 3 | 1 | 2 | 2 | 2 | 0, 1, 2 | no |
| C2, P3m, P4m | 3 | 3 | 3 | 3 | 3 | 0, 0, 1, 2 | yes, certified by forced singletons |
| C3 | 3 | 3 | 3 | 3 | 3 | 0, 0, 1, 3 | yes |
| C4 | 4 | 4 | 4 | 4 | 4 | 0, 0, 1, 2, 4 | yes |
| O1 | 5 | 2 | 4 | 5 | 5 | 0, 0, 1, 2, 2, 3 | **yes, and the disjoint bound misses it** |
| O2, O3 | 6, 7 | 2 | 4 | 5 | 5 | 0, 0, 1, 2, 2, 3 | no |
| O1c, O2c, O3c | 5, 6, 7 | 2 | 4 | 4 | 4 | 0, 0, 1, 2, 3 | no |
| B23 | 5 | 5 | 5 | 5 | 5 | 0, 0, 1, 2, 4, 6 | yes |
| B33 | 6 | 6 | 6 | 6 | 6 | 0, 0, 1, 2, 4, 6, 9 | yes |
| T22 | 5 | 2 | 4 | 4 | 4 | 0, 0, 1, 2, 4 | no |
| D1 | 6 | 0 | 3 | 3 | 3 | 0, 0, 2, 4 | no |

### What the predictions say, in words

- **C1 against C2.** Shifting the repeat by one raises the U minimum from 2 to 3 while the program rank
  stays 2. Under W2 it turns a corpus that needs fewer entries than characters into one that needs all
  three.
- **O against its control.** The motif needs 5 entries under W2 and its control needs 4. The disjoint
  bound says 4 for both and cannot tell them apart. The block rank says 5 and 4.
- **O1.** The minimum equals the alphabet size, 5, but no disjoint witness reaches 5. This is the kind of
  corpus the saturation certificate misses.
- **C4, the grids and T22.** The program rank is one less than the U minimum. No program has a cuttable
  prefix, so the rank limit cannot be attained.
- **D1.** Four programs are spelled with three entries, the program rank. Two entries already spell two
  programs.

### Ablations

- **Terminator.** T22 against C4: appending `$` leaves the W2 minimum at 4 while the alphabet grows from 4
  to 5, so the corpus stops needing one entry per character. The U minimum stays 4 and the program rank
  stays 3.
- **Whole programs allowed as entries (U only).** C3: minimum 3, curve 0, 1, 2, 3. C4: minimum 4, curve
  0, 1, 2, 3, 4. With the exclusion the curves are 0, 0, 1, 3 and 0, 0, 1, 2, 4.

## Baselines

Every predicted minimum is reported beside four simpler numbers: the alphabet size, the forced
singletons, the rank alone (program rank under U, block rank under W2), and the disjoint bound alone.

## Random search family

`instances.json` also holds 200 corpora of three programs, each 3 to 5 characters over `a`, `b`, `c`,
drawn from a fixed stream. No prediction is made for an individual corpus.

- S1 to S6 must hold on all 200.
- A\* is tested in the form "the W2 minimum equals the larger of block rank and disjoint bound".
- B\* is tested in both directions.
- The count of corpora where each holds is reported, and the first counterexample to each is published
  with its programs.

## What falsifies what

| Outcome | Consequence |
| --- | --- |
| Any of S1 to S6 fails on any corpus | A theorem or a checker is wrong. Stop and report before anything else. |
| A predicted number differs from exhaustive enumeration | Published as a miss with the instance, whichever side erred. `predictions.json` is not edited. |
| A frozen instance has a W2 minimum above its block rank | A\* is false. The instance is published. |
| A frozen instance has every program cuttable and a U minimum above its rank | B\* is false. The instance is published. |
| O1 has a disjoint witness of size 5, or a W2 minimum below 5 | The claimed gap in the saturation certificate is not there. |
| An O pair has the same W2 minimum | The overlap motif does not do what is claimed. |

## How the predictions will be checked

- Minimums and curves by exhaustive enumeration of dictionaries, smallest first. Every instance here is
  small enough.
- Where an optimum cannot be enumerated in a later, larger family, a certified interval is reported
  instead.
- The evaluator is committed before it is run on any frozen instance. Its own tests use only corpora
  outside this file.
- Results are published in full, misses included, in this folder.

## What was already known when this was written

- **O2** is the motif already in `capacity-impossibility-v1`. Its W2 minimum of 5 and disjoint bound of 4
  were known. Everything else about it here is a prediction.
- The matched80 results, and the `aaa` and `aaa`/`aab` regressions, were known. They are not instances
  here.
- Nothing was run on any other instance in this file.
