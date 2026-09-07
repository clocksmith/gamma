# MIDAS opening250KB terminal audit

[Terminal receipt](../midas_open_observed_sha_opening250k_terminal_20260907.json)
and [validated reflection](../../adaptive/reflections/20260907T201808Z_5c99705f63.json)
record the closed missing-boundary comparison. P/K are 115,921 archive bytes,
F is 107,176 and S is 119,779. These reproduce the historical result; complete
package and full-corpus score remain unknown.

Run from `/home/x/deco/gamma/projects/enwiki9`:

```bash
PYTHONPATH=/home/x/deco/gamma python3 -B \
  operations/provenance/midas_open_observed_sha_opening250k_terminal_20260907/record.py \
  --closed-job operations/adaptive/completed/909_20260907T201808Z_5c99705f63.json \
  --job-sha256 854c58a4744509e145e06b523e76c4871a86def2ea4e5ffc8869db517888a7ab \
  --guard-sha256 20612e1471aff8bfe7d0761086ce8e9d6b4c1d2dec8611dd9eb64ea69fb14e47 \
  --closure-authorized > /dev/null
```

Exit zero means the normalizer's closed-source, artifact, inversion, repeat,
probability, boundary, accounting and guard checks pass. It reads retained
evidence and launches no codec. `PYTHONPATH` resolves Gamma's research-contract
imports; `-B` suppresses bytecode writes. Remove the final redirection to inspect
the recomputed canonical records on stdout; the command publishes no files.

The closure flag applies to this exact completed job and closed guard. It is
not authority to inspect an active job or launch a successor. Fresh distant250KB
confirmation requires its own frozen inputs and admission.

The first validated reflection omitted the recorder's required direct index
reference. Its exact bytes are preserved in
`reflection_before_index_binding.json`; the current reflection adds that index
and preservation link, with its verdict and measurements unchanged.
