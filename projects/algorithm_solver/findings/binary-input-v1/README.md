# Binary-input study v1

Component: algorithm_solver. Intent deliberately extended to the user-requested
input-encoding study; solver evaluation boundaries are preserved. 256one owns
UI/runtime packaging, not Gamma. This does not activate a model or solver campaign.

- [Source acquisition](source-summary.json): pinned JS/TS files with full per-file
  manifest in ignored remote raw data. Original license and README retained there.
- [Python encoding](python-summary.json): train-only vocabulary fit, then one
  development score. No human speed or optimal-vocabulary claim.
- `runs/binary-python-v1/` contains the profile and reference rows/provenance.
- `runs/binary-challenges-v1.json` contains the metadata-only navigation export.

Run from `projects/algorithm_solver` with the existing Python environment:

```sh
python -m algsolve.input_corpus
python -m algsolve.input_vocabulary --confirmation runs/mine-v2-candidates-20261017/split.json --output runs/binary-python-v1
python -m algsolve.input_catalog --output runs/binary-challenges-v1.json
```

Do not refetch or overwrite a retained run to claim fresh evidence. Raw references
and run files remain ignored; only compact receipts and tools are committed.
Download authority in this session covered additional reference sources, not model
weights, installs or paid services. New sessions retain Gamma's approval policy.

Acceptance evidence: touched Python modules compile; two focused unittest cases
include 255 encodings checked against independent exhaustive segmentation and
all-ASCII coverage. Website verification lives in 256one; finite codec tests do
not qualify the underlying algorithm solutions or independent solver performance.

Next: fit and compare a JS successor from the pinned corpus, separately consider
TS-derived JS after conversion validation, and measure actual human navigation,
corrections and presses. Preserve existing learned codes until choosing a new
version explicitly. No hidden tests or expected outputs belong in the website.
