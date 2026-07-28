# JANUS Paid Residual MDL 10M Trace Plan

Date: 2026-07-28

Candidate: `janus_paid_residual_mdl_q0_v1`

Purpose: zero-credit infrastructure required by the authorized frozen 10M
JANUS gate.

## Bound parent

Use the clean-build endpoint428 program already bound by the native 1M and 10M
receipts:

`/home/x/enwiki9-nonproof/results/cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/clean-build-b/comp9a-decomp9`

Use the canonical 10M input:

`/home/x/enwiki9-nonproof/gamma/projects/enwiki9/data/enwik9_10000000.bin`

The trace-off identity target is:

`/home/x/enwiki9-nonproof/results/endpoint428_pair_layer0_online_native_10m_v1/archive.bin`

Its recorded size is 1,635,174 bytes and its SHA-256 is
`dddc0d0e4824433c605d870470d80bb119292b465689d0381933b37c5fb0e8d9`.

## Gate

1. Produce the exact WRT stored stream with the same clean-build backend and
   dictionary using the backend's `-s` mode.
2. Compress the canonical 10M input with `CMIX_P1_TRACE` enabled.
3. Enforce the decimal 10GB single-process memory limit with
   `run_with_rss_guard.py`.
4. Require a clean process exit and no memory violation.
5. Require the trace-enabled archive size and SHA-256 to equal the existing
   trace-off archive exactly.
6. Bind the input, binary, dictionary, WRT store, trace, archive, guard, and
   reference archive by SHA-256 in a machine-readable decision.

The trace has zero score credit. It authorizes only the already frozen JANUS
10M oracle. It does not authorize an integer decoder, native integration,
larger corpus run, or change to the JANUS architecture.

