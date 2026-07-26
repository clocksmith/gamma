# Clockwork residual-expert Gamma gate

This directory is Gamma's independent acceptance lane for
`clockwork.residual_expert_search.v1`.

The import bundle under `imports/m3t4-e6d0ed9d/` binds one M3T4 frontier
candidate, its Gamma-authored challenge, frozen development trace, advisory
search receipt, and the full upstream Git revision. `import-manifest.json`
hashes each imported byte stream. The Gamma-owned `transfer-trace.json` is not
part of M3T4's search population.

Reproduce the receipt:

```bash
python3 projects/enwiki9/tools/clockwork_candidate_gate.py gate \
  --bundle projects/enwiki9/operations/clockwork/residual_expert_search_v1/imports/m3t4-e6d0ed9d \
  --output projects/enwiki9/results/clockwork_residual_expert_7714969866c6/receipt.json
```

Gamma validates canonical contracts and import hashes, then independently
reimplements chronological evaluation in Python. It checks roundtrip identity,
the literal fallback, M3T4/Gamma ledger agreement, transfer, package size,
runtime, and memory before emitting `gamma.candidate_receipt.v1`.

The accepted receipt proves only this bounded synthetic bridge challenge. Its
ledger uses integer Brier-loss units and explicitly sets
`compressionBytesClaimed` to false. It gives no enwiki9 byte-score, Hutter
frontier, theorem, Seal, or full-corpus credit.
