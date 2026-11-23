# `witness-length-sweep-v1`: Pre-registered `K x L` Capacity Sweep and Unseen Transfer

Sweeps vocabulary budget `K` against maximum entry length `L in {1, 2, 4, 8, 16, 32, 160}` under the length-capped witness rule `W(L)` on:
1. Frozen `matched80` compact (`N = 80`, `|Sigma| = 92`, Gamma commit `59ff04415ff2afd04ff2ed451340f4f02852bf18`), comparing deterministic frequency-picked baselines, exact single-character sets, best verified `W(L)` dictionaries, and 100% solver-free proven upper bounds.
2. Disjoint frozen `-a -> -b` transfer pairs (`J-80`, `P-80`, `J-160`, `P-160` from `../witness-scaling-v1/cohorts.json`), testing whether dictionaries frozen on `-a` yield a repeatable unseen-program coverage advantage on `-b`.

## Verify solver-free

```sh
shasum -a 256 -c SHA256SUMS-FROZEN
shasum -a 256 -c SHA256SUMS-TRANSFER-FROZEN
shasum -a 256 -c SHA256SUMS-RESULTS
python3 -B check_length_sweep.py /path/to/gamma
python3 -B check_unseen_transfer.py
```

See `PREREGISTRATION.md`, `PREREGISTRATION-TRANSFER.md`, and `RESULTS.md` for full pre-registered predictions and scored outcomes.
