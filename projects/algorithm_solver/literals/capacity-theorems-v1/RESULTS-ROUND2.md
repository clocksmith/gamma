# Results, round two, and the first counterexamples

Round-two pre-registration: Gamma `49e251a3`, committed before the family was run. `results-round2.json`
has the tallies. The counterexamples below were built afterwards by reasoning and then checked with the
same evaluator; they are in `counterexamples-after-round2.json`.

## Both conjectures are false

| Conjecture | Counterexample | Numbers |
| --- | --- | --- |
| A\* as first stated: the witness-rule minimum equals the block rank | `axby`, `byax`, `aybx`, `bxay` | block rank 3, minimum 4 |
| A\* in its stronger form: the minimum equals the larger of block rank and disjoint bound | `abd`, `abe`, `fbd`, `pxqy`, `qypx`, `pyqx`, `qxpy` | block rank 8, disjoint bound 8, minimum 9 |
| B\*: the unrestricted minimum equals the program rank whenever every program has a cuttable prefix | `axby`, `byax`, `aybx`, `bxay` | every program cuttable, program rank 3, minimum 4 |

- **Neither lower bound dominates.** In `abd`, `abe`, `fbd` the block rank is 5 and the disjoint bound 4.
  In the four-program corpus the disjoint bound is 4 and the block rank 3.
- **Their maximum is not tight either.** Both bounds add over corpora that share no character, and so does
  the minimum. Joining a corpus where one bound is loose to a corpus where the other is loose leaves both
  loose. The seven-program corpus is exactly that join, and it needs all 9 of its characters with neither
  bound saying so.
- **A cuttable prefix is necessary, not sufficient.** The proved half of B\* (S5) stands. The other half
  does not.
- The counterexamples were not found by the frozen families. They came from asking why the two bounds
  complement each other on the frozen instances.

## Round two itself

150 corpora of three or four programs built from shared two-character blocks.

- **No proved claim fails** (S1 to S6) on any corpus.
- **A\* holds on 150 of 150** in its stronger form. The block rank alone equals the minimum on all 150; the
  disjoint bound on 148; the forced singletons on 11.
- **B\* holds on 150 of 150.** Nine corpora have a minimum above their program rank, and each has a
  program with no cuttable prefix.
- 144 of the 150 need every character under the witness rule. In two of those the disjoint bound is
  smaller than the alphabet, for example `acbd`, `bdacb`, `cbdbd` (alphabet 4, disjoint bound 3).

### Expectations stated beforehand

| Expectation | Outcome |
| --- | --- |
| B\* fails on at least one corpus | **Wrong.** It held on all 150. |
| A\* holds on at least nine in ten and fails on at least one | **Half wrong.** It held on all 150. |
| Some corpus needs every character while its disjoint bound is smaller | Right: two corpora. |

The family was still easy: 135 of 150 corpora have a minimum equal to the alphabet size under the witness
rule and equal to the rank under the unrestricted rule. A random family of this kind does not reach the
structures that break the conjectures.

## What stands after both rounds

- The six proved claims held on all 368 corpora evaluated (18 frozen, 200 and 150 random).
- The disjoint bound and the block rank are each valid, each sometimes strictly better than the other, and
  their maximum can still be one short.
- Under the unrestricted rule, "every program has a cuttable prefix" is a necessary condition for a
  dictionary of rank size, and it is checkable without search. It is not a characterization.
- A characterization of when the minimum equals the alphabet size is still open. The seven-program corpus
  is the smallest example found so far that any proposed criterion must handle.
