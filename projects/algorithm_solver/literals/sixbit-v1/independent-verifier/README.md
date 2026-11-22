# Independent BITS compact certificate checker

From the root of a clean Gamma checkout that contains the frozen source commit:

```sh
python3 -B projects/algorithm_solver/literals/sixbit-v1/independent-verifier/check.py
```

Requires Python 3.9+ and Git. Pass another Gamma checkout as the optional argument. If
`59ff04415ff2afd04ff2ed451340f4f02852bf18` is absent (for example, a shallow clone),
fetch it first. The checker itself does not fetch, run JavaScript, run an optimizer,
invoke an existing checker, or write to the checkout. It reads the pinned Git objects,
not mutable paths, and checks both qualification receipts against the exact compact
source bytes. It does not rerun those qualification tests.

| Objective | W | U |
| --- | ---: | ---: |
| A: minimum exact dictionary | 92, tight | 79, tight |
| B: maximum coverage with 64 entries | 64/80, tight | 64/80, tight |
| C: frozen presses with 63 entries plus ESC | 75,925, tight | 24,166 lower bound; 24,613 feasible, gap open |

A uses a fresh reachability traversal to recover a valid concatenation of the
manifest vocabulary for each of the 80 programs. There are no A six-bit packets:
neither A dictionary fits in 64 slots. B and C parse binary LTD1 dictionaries and
LTV1/LTE6 packets independently, require exact ordered dictionary/manifest
agreement, then compare reconstructed bytes to the frozen source for each problem.
The B/U witness is the Jupiter supplement; the other rows use the frozen Mars run.

## Why the integer certificate works

Each segmented source is a path from position 0 to its last character boundary.
Let `D` be the positive scale, `p_i` the stored integer potential for position
`i`, and `mu >= 0` the stored scaled budget multiplier. The telescoping difference
`p_0 - p_n` is extracted from each path. Each arc of scaled cost `c` then has
reduced cost `c - (p_i - p_j)`. For each eligible string, group its eligible
occurrences. If its dictionary slot is unused, its group contributes zero. If used,
the group's cost is bounded below by the scaled slot price minus the sum of
positive reductions over **all** occurrences (a path cannot use an occurrence
more than once). Take the smaller of those two bounds. Repeated occurrences of
any string use the same slot, even in one problem. W checks distinct problem IDs
for multi-character witnesses; U uses every proper non-whole substring.
Neither procedure uses a solver's pruned arc inventory.

- A: literal arc cost 0, slot price `D`, and no dictionary budget multiplier.
- B: literal arc cost 0, slot price `mu`, budget 64. Each program can instead
  take its uncoupled omission arc costing `D`. The minimization objective is
  the number of omitted programs.
- C: literal arc cost `7D`, slot price `mu`, budget 63. An uncoupled
  one-character ESC arc costs `15D` and exists only for permitted ASCII/newline.

Each uncoupled arc contributes the smaller of 0 and its reduced cost. Subtract
`mu * budget` for B/C. This establishes a rational lower bound by relaxing
coupling and path constraints; only integer arithmetic is used. The checker
rounds upward for A/C and subtracts the rounded omission bound from 80 for B,
then compares against the independently feasible witness and frozen integer
claim. A changed potential vector need not be invalid: it is rejected only if
it does not substantiate the exact published claim (or is malformed).

The output's `tight` applies only to its named objective, not B phase-2
selections, package sizes, raw press optimality, canonical programs, unseen
programs, or human input speed.

## Test in one command

```sh
python3 -B -m unittest discover -s projects/algorithm_solver/literals/sixbit-v1/independent-verifier -v
```

Includes exact frozen reproduction, exhaustive tiny vocabulary/path oracles,
weak duality for varied potentials, codec envelope rejection, and a mutation
suite. The mutations rebind affected packet/dictionary or source/receipt hashes
where applicable, so a superficial unrefreshed manifest hash does not explain
rejection.
