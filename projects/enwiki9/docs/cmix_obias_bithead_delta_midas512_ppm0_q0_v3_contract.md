# Bit-Head DELTA-MIDAS 512 + PPM0 q0 v3

v3 is a prospective composition; it has not been compiled or measured. It
does not change the sealed v2 learning direction, rank, segment coordinate,
quantizer, clipping, step sizes, controls, injection points, or reset cadence.
It adds only the sealed compile-time PPM residency policy:

```text
-DCMIX_PPMD_RSS_BUDGET_MB=0ULL
```

The complete scientific realization remains defined by
`cmix_obias_bithead_delta_midas512_q0_v2_contract.md`. The memory realization
remains defined by `cmix_obias_ppm_always_purge_q0_v1_contract.md`. The v3
composition file binds both candidate-tree identities and the exact build
order.

All `C/P/K/O/R/D/S` builds use the budget-zero policy, so memory behavior is
matched across arms. `C` is the clean-source build control. `P` adds only v2
observation. `K` computes the full eligibility sidecar with zero injection.
`O/R/D/S` retain their sealed v2 meanings. Required gates are:

```text
C payload == P payload
P probability/state/payload == K probability/state/payload
each arm repeat archive and exact inverse
each encode/decode probability/state receipt synchronized
all controls live and finite
D payload < P,K,O,R,S
incremental package <=65,536 bytes
every process-tree peak RSS <9,765,625 KiB
all scratch cleaned
```

The opening 250KB population is diagnostic only. Passing it authorizes only a
prospectively frozen 1MB successor, followed by opening and distant 10MB gates,
100MB, and isolated full-corpus qualification. A full result receives credit
only for actual counted archive reduction after paying every required binary,
model, table, and dependency byte. The external CMIX substrate remains fully
attributed and receives zero Gamma authorship or score credit.
