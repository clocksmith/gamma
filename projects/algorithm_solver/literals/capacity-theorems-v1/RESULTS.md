# Results, round one

Pre-registration: Gamma `69d4c1fe`. Evaluator committed before use: Gamma `f4087bba`. Evaluated once, by
exhaustive enumeration. `results.json` has every observed number.

## Frozen instances

- **220 predicted numbers, 0 differ.** Every alphabet size, rank, forced-singleton count, disjoint bound,
  minimum and coverage curve matches, for all 18 instances under both rules and for the two ablations.
- **No proved claim fails** (S1 to S6).
- **A\* holds on 18 of 18:** the witness-rule minimum equals the block rank.
- **B\* holds on 18 of 18:** the unrestricted minimum equals the program rank exactly when every program
  has a cuttable prefix.

The contrasts the instances were built for are all there:

| Contrast | Observed |
| --- | --- |
| `abc`, `abab` against `abc`, `baba` | Unrestricted minimum 2 against 3 with program rank 2 in both. Witness-rule minimum 2 against 3 with three characters in both. |
| Overlap motif against its abutting control (three sizes) | Witness-rule minimum 5 against 4. Disjoint bound 4 in both. Block rank 5 against 4. |
| `abd`, `abe`, `fbd` | Needs all 5 of its characters; the largest disjoint witness has 4. The saturation certificate misses it; the block rank does not. |
| `ax`, `ay`, `bx`, `by` and the grids | Program rank one below the unrestricted minimum; no program has a cuttable prefix. |
| `abcd`, `abef`, `efcd`, `cdef` | Three entries spell four programs, the program rank. Two entries spell two. |
| Terminator appended to the 2 by 2 grid | Alphabet 4 to 5; witness-rule minimum stays 4. |
| Whole programs allowed as entries | Curves become 0, 1, 2, 3 and 0, 1, 2, 3, 4. |

## Random family

- 200 corpora. No proved claim fails. No counterexample to A\* or B\*.
- **This family could not have falsified either conjecture.** In 194 of the 200 corpora the alphabet size,
  both ranks, the disjoint bound and both minimums are all 3; in 5 they are all 2. Only one corpus has an
  unrestricted minimum above its rank (`bbca`, `bccb`, `ccaa`: rank 2, minimum 3), and it has a program
  with no cuttable prefix, as B\* says.
- Three short random strings over three letters almost always need every letter. A family with shared
  blocks and overlaps is frozen as round two before it is run.

## What this does and does not show

- The hand analysis and the evaluator agree on every number, and the planted contrasts are real.
- The 18 instances were designed by the author of the predictions. Agreement there is not evidence that
  A\* or B\* hold on corpora chosen without those conjectures in mind.
- Nothing here bears on key presses or typing speed.
