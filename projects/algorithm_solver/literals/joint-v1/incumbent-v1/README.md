# Preserve feasible incumbents during joint literal search

Goal v2:2b. A larger source-choice space must not discard a valid, better
fixed-source result. `incumbent.py` validates the imported cohort, objective,
dictionary cap, candidate pool, source choices, exact packets and full costs.
It resegments permitted alternatives, then retains the best verified state
even when a heuristic returns a worse terminal state. It never executes source.

The objective is lexicographic: maximize coverage, minimize selections, then
minimize dictionary plus packet bytes. Complete input bits, library installation
bytes and decoder storage remain separate reported quantities. This objective
is not a universal human-usability score or a global-optimality certificate.

`optimizer.py` adds an accepted-state observer to the bounded existing search.
Its historical candidate ranking and default add/remove/swap ordering are preserved. The shared
[`reachable_core.py`](../reachable_core.py) retains the historical 96-character
default while allowing an explicit empty mandatory basis and fail-closed
unreachable-source results. The codec is the existing
[`literal_codec.py`](../../readable-v1/literal_codec.py).

Run focused synthetic controls from any checkout:

```sh
python3 -B projects/algorithm_solver/literals/joint-v1/incumbent-v1/test_incumbent.py -v
```

These 21 tests include invalid identities, stale or forged costs, lost coverage,
changed packets, worse terminal trajectories and integration with the real
optimizer. They do not execute or qualify candidate programs. The portable
adaptation changes dependency paths and CPU-affinity selection only; original
experiment code and receipts remain immutable under the recorded hashes.

## Measured development follow-up

Four warm-start arms reused the already audited fixed-source winners for the
same 16 problems (4 Easy, 9 Medium, 3 Hard). All four retained exactly their
incumbent costs after 80 additional trials; no rewrite or compression improvement
was found. The new run used 1.096 CPU seconds, with 41.4 MB peak child RSS.
Acquiring the earlier winners required a separate 62.053-second, 9,744-trial
experiment. Reusing it is not an equal-compute cold-start comparison.

| Language / width | Entries | Selections | Complete input bits | Library bytes | Library + packets |
| --- | ---: | ---: | ---: | ---: | ---: |
| JavaScript / 7 | 128 | 8,480 | 64,648 | 2,059 | 10,140 |
| Python / 7 | 128 | 7,398 | 57,088 | 4,388 | 11,524 |
| JavaScript / 8 | 256 | 3,607 | 34,104 | 10,832 | 15,095 |
| Python / 8 | 250 | 3,417 | 32,584 | 11,700 | 15,773 |

The common 8,240-byte decoder is separate. Coverage is 16/16 in each row; no
whole-program entries are allowed. This preserves the previous input/storage
tradeoffs and the failed joint trajectories. The search stopped after testing
its bounded local proposals, not after proving an optimum. Readable and six-bit
controls remain separate unchanged experiments.

This follow-up verifies encoding, not new problem correctness. Ten of the added
implementations have historical executable/runtime identities; six retain
source/test/harness evidence without complete executable identities. No new
source execution, admission, held-out evaluation, model training, public push
or BITS promotion occurred. It does not satisfy M1.

The next justified comparison is a separately frozen proposal-ranking change,
for example distinguishing gains on selected parses from alternative-enabling
proposals, with the same incumbent and charged search budget. More framework or
a larger candidate space alone is not a measured gain.

See `evidence.json` for source and receipt hashes. Private source pools, original
test bodies, dictionaries and program packets are intentionally external inputs;
they are not included in this code-and-aggregate checkpoint.

## Canonical six-bit and UTF-8 successor

The supported incumbent adapter now accepts explicit 6/7/8-bit tables and UTF-8
sources/dictionaries while preserving the unchanged historical codec and exact
core. Six bits means at most 64 entries, without an implicit character basis or
raw-source escape. Existing identity, coverage, source-choice and packet gates
remain in force. Synthetic UTF-8/CRLF controls do not qualify real programs.

`optimize(..., swap_policy="balanced")` optionally distributes the eight swap
proposals across all four shortlisted additions and removals. The default remains
`legacy`; this fixes shortlist participation, not a proven compression advantage.
The earlier source-as-data comparison using an independently implemented
compatible codec found no retained-cost gain from this policy. It is not a new
canonical-codec performance result. `exact_evaluations`, `trim_evaluations` and
occurrence substring scans are now reported separately from proposal trials;
forward audits, observer validation and complete runtime retain separate costs.

Run `python3 -B test_successor.py` from this directory for 13 focused controls:
64 versus 65 entries, UTF-8 exact packets, cache/full-DP parity, incumbent retention,
bounded schedules and canonical packet golden vectors. The unchanged 21 incumbent
and 30 energy mechanism tests also pass with the canonical codec. No candidate
program execution, admission, protected evaluation or human-fluency claim follows.
