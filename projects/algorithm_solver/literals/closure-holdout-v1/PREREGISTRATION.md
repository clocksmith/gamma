# closure-holdout-v1: is the BPE advantage on unseen code its structure or its objective?

Status: preregistered. Written and committed before any test set below was selected or opened.

## Question

objective-holdout-v1 found a reversal. Greedy token-gain selection (`token`) uses fewer tokens than byte pair
encoding (`bpe`) on unseen CodeNet code with 84 fragments, and 7.7% more with 3,924, although it uses 22.0%
fewer in training. Removing its single-problem fragments erased the training lead but left it 10.7% behind BPE
on unseen code. That ablation changed the dictionary size, so it could not say why BPE generalizes.

BPE differs from token gain in two ways at once:

- **Objective.** BPE adds the most frequent adjacent pair of its current segmentation. Token gain adds the
  string that most reduces the exact minimum number of training tokens.
- **Structure.** Every BPE entry is the concatenation of two earlier entries, so the dictionary is closed under
  its constituents. Token gain may add any substring, so a long entry can arrive without the shorter pieces
  that would still match when the long one does not.

This experiment separates the two with one new arm, `closed`: the token-gain objective with BPE's structure.
A string becomes a candidate only once it is the concatenation of two members of the current dictionary
(single bytes are members); among candidates, the one with the largest exact training token gain is added.

## Arms

All three use the objective-holdout-v1 candidate pool (every substring of 2 to 16 bytes inside one training
file, policy `s1-whole`), the training split CodeNet `primary` (200 problems, 400 files, 259,706 bytes), the
171-byte training alphabet, one escape, and caps of 256 and 4,096 symbols (84 and 3,924 multi-byte entries).

| Arm | Objective | Structure | Source |
| --- | --- | --- | --- |
| `bpe` | pair count in its own segmentation | closed | frozen engine `bpe` |
| `token` | exact training token gain | open | frozen engine `greedy-entry` |
| `closed` | exact training token gain | closed | `engine_closed.c`, mode `greedy-closed` |

`engine_closed.c` includes the frozen `fixed-source-v3/engine.c` unchanged (SHA-256 `7331f1eb…b19f`), so
enumeration, the shortest-path cost and the gain computation are the code that built objective-holdout-v1.
`train.py` stops unless the `bpe` and `token` dictionaries it builds equal the frozen objective-holdout-v1
dictionaries entry for entry at both caps. They do.

## Development evidence (seen before writing this file)

Only `train` and `dev` (CodeNet `secondary`, 200 problems) were scored. Tokens relative to `bpe`, exact parse:

| Fragments | 84 | 400 | 1,408 | 2,000 | 3,924 |
| --- | --- | --- | --- | --- | --- |
| `token`, train | −13.1% | −12.2% | −12.9% | −14.7% | −22.0% |
| `closed`, train | −0.4% | −0.4% | −1.5% | −1.8% | −2.6% |
| `token`, dev | −11.9% | −10.8% | −3.9% | −0.9% | +6.4% |
| `closed`, dev | −0.3% | −0.2% | −1.5% | −1.7% | −1.5% |

On dev the share of tokens that are single bytes or escapes falls with size for `bpe` (70.0% to 25.3%) and
`closed` (69.7% to 23.7%), but stops falling for `token` near 34% from about 1,400 fragments on.

Reading: under closure, the gain objective beats BPE at every size on dev; without closure the gain objective
wins while slots are scarce and loses once they are not. The development evidence is the reason for the rules
below, so it is not evidence for them.

## Test sets

Decisive sets are new, selected by the scorer after `frozen/` is committed, by rules fixed in this commit:

- **`fresh2`** (`select_fresh2.py`): 200 CodeNet problems, the objective-holdout-v1 `fresh` ranking continued
  past its last rank, excluding IBM identical-problem clusters of any earlier problem, exact or
  whitespace-only duplicates of any earlier file, and files with 8-byte shingle Jaccard of at least 0.8 with an
  earlier file of the same language. Earlier means `primary`, `secondary` and `fresh`. One Python and one
  JavaScript file per problem, by the frozen median-length pick.
- **`project-python`, `project-javascript`** (`select_projects.py`): for each language, the first repository in
  the frozen objective-holdout-v1 candidate order, other than Express, with at least 40 eligible files; at most
  200 files by the frozen file order; duplicates of any earlier file dropped and counted.

The objective-holdout-v1 test sets `fresh` and `project` (Express) are scored too and reported as replications
on sets already used for the earlier experiment. They decide nothing here. The trainer has not scored any arm
on them for this experiment.

## Scoring

`score.py` with the frozen dictionary hash. Per set, arm and cap: exact minimum tokens (an escaped byte is one
token), the share of single-byte or escaped tokens, and the equal-size grid of the 4,096 orders at 84, 200,
400, 600, 900, 1,200, 1,408, 1,700, 2,000, 2,350, 2,700, 3,300 and 3,924 fragments. Paired per unit (CodeNet
problem: its two files summed; project: file), two-sided sign test, ties dropped. Tokens only; archives are not
part of this experiment.

## Decision rules

A difference under 1.0% counts as none. `fresh2` decides S, O, P, F and G; projects decide J and are never
pooled with CodeNet.

| Id | Statement | Holds if |
| --- | --- | --- |
| **S** | Structure explains the large-budget deficit | On `fresh2` at 4,096, `closed` uses at least 1.0% fewer tokens than `token`, and is lower on more problems than higher, sign p < 0.05 |
| **O** | Under closure the gain objective beats BPE | On `fresh2` at 4,096, `closed` uses at least 1.0% fewer tokens than `bpe`, lower on more problems, sign p < 0.05 |
| **P** | Open selection wins when slots are scarce | On `fresh2` at 256, `token` uses at least 1.0% fewer tokens than `closed`, sign p < 0.05 |
| **F** | The mechanism is fallback | On `fresh2` at 4,096, the single-byte share of `closed` is below that of `token` |
| **G** | Closed never loses to BPE at equal size | On `fresh2`, `closed` uses no more tokens than `bpe` at every grid size |
| **J** | Structure transfers to whole projects | Per project, at 4,096, `closed` uses at least 1.0% fewer tokens than `token`, lower on more files, sign p < 0.05 |

How the paper follows:

- S, P and F hold: the crossover is a structure effect. Open selection wins when slots are scarce; closure wins
  once they are not, because long open entries leave unseen text to single bytes. That is the result.
- O also holds: a rule that keeps BPE's structure and uses the exact objective beats BPE at the size where
  token gain lost. Report its size, and that it is small.
- S fails: closure is not what BPE has; the reversal needs another explanation. Say so.
- J failing on a project while S holds: the structure effect is specific to CodeNet-like code.

## Order of work

1. This file, `engine_closed.c`, `train.py`, `select_fresh2.py`, `select_projects.py`, `score.py`, `dev_eval.py`
   and `frozen/` are committed and pushed. `frozen/dictionaries.json` has SHA-256
   `4f2d4410f6e6a841fbd01783ec9a0f03498f40f356d9f2996642debe0ba543b7`, also pinned in `score.py`.
2. A scorer that did not build the arms runs `select_fresh2.py`, then `select_projects.py`, then `score.py`,
   logs every command and its output in `SCORER-LOG.md`, and commits `sets/`, `corpus/`, `out/` and the log.
   It changes no committed rule. A failure is logged and stops the run.
3. Results are written up against the rules above. Any later analysis is labelled post hoc.

## Isolation

The builder (this commit) and the scorer are separate agent sessions on the same machine and model family.
The builder has not opened `fresh2`, either new project, or any score of `closed` on `fresh` or Express. The
test sets are fixed by seeded rules committed here, so the builder cannot choose them. A same-family scorer is
not an independent evaluator; this is a preregistered dev-free holdout, not an external replication.
