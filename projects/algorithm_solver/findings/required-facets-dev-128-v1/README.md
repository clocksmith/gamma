# Required facets: bounded development candidate on 128

The opt-in [required-facet gate](../../algsolve/required_facets.py) now rejects a
non-exact selected source when a declared answer-changing query requirement is
missing, contradictory or uncertain. This implements the next correction from
the retained [post-fresh diagnosis](../post-fresh-diagnosis-suby-v1/README.md).
The original contradiction-only policy and default answer route remain unchanged.

The gate runs after the existing identity check and before source approval and
public execution. It never replaces the selected candidate. Missing/stale source
contracts abstain; source facts and public examples cannot supply missing query
facts. Exact statement/interface matches retain the existing path. No questions,
generated fallback, model calls, training or downloads are added.

[Ten source contracts](../../contracts/required_facets_dev_128_v1.json) explicitly
require trade count, fee, cooldown and output for stock; output, update mode and
duplicate semantics for rank. All ten statement hashes were checked against the
existing local corpus. These implementer declarations are necessary conditions,
not an independently reviewed or complete semantic description. The narrow parser
does not support every declared value, and all other non-exact sources abstain.
Broad coverage loss remains unmeasured. Do not promote this candidate.

## Evidence

- Focused policy checks: 19 tests and 50 subtests passed.
- Required judge/lane checks: 33 tests passed, including isolation checks.
- [Reproducible synthetic audit](audit.py), [per-case results](behavior.json):
  fixed retrieval and a test approval stub, actual sandbox public execution.
  Control answered 12/12; candidate answered four complete requests and abstained
  on all eight requests requiring abstention. Zero complete requests were lost
  in this deliberately small developer-exposed set. The four returned programs
  passed eight additional developer-authored checks, including duplicate ranking
  and repeated-trade distinctions. Only two fixed stored implementations were used.

This is a software/development behavior result. It does not measure learned
retrieval, generalization, real library approval, performance or unseen solving.
The consumed fresh36 result remains 16 correct, two wrong acceptances and 18
abstentions, with no replay. Original checkpoint comparison remains raw/corrected
4/10 fit, nearest 8/10 fit, all 0/8 audit. No protected cases were opened and no
new composition improvement is claimed.

## Explicit entry point

From Gamma, use the existing approved-library manifest and a JSON Problem:

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false \
PYTHONPATH=projects/algorithm_solver .venv_rocm/bin/python -m algsolve.required_facets \
  query.json --approved-library /path/to/approval.json \
  --contracts projects/algorithm_solver/contracts/required_facets_dev_128_v1.json
```

Historical approval manifests may reject changed source fingerprints; preserve
that rejection and make a separately qualified candidate instead of changing old
receipts. The Python entry point additionally accepts the existing opt-in
contradiction policy. All previous numeric, source-approval and public-example
gates still apply. This command is not a selected release configuration.

To reproduce the synthetic behavior receipt without models:

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
PYTHONPATH=projects/algorithm_solver:projects/algorithm_solver/tests \
.venv_rocm/bin/python projects/algorithm_solver/findings/required-facets-dev-128-v1/audit.py
```

## Remaining work and authority

Review the limited facet declarations and parser uncertainty behavior, then measure
useful versus harmful abstention on permitted development data with actual pinned
retrieval and approval. Freeze a new candidate before a separately authored,
reviewed and unopened recognition set. Existing protected composition scoring
and autonomous-loop gates remain closed. New training still requires owner
approval and a qualified full-text encoding policy for the two oversized inputs.

Machine identity was reverified as x@128. Existing Reploid workloads remained
active, so this change used deterministic checks without performance measurement.
Component intent is preserved; the only new boundary is an explicit opt-in
necessary-requirement rejection within stored recognition. Original failures,
sources, assets and conflicting candidates remain intact.
