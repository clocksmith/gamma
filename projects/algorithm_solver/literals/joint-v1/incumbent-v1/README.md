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
Its candidate ranking and add/remove/swap moves are unchanged. The shared
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
