# Independent persistent timing readback

`verify.py` checks final report / incremental JSONL / progress / supervisor
consistency against the exact freeze. It validates 8 description and 6 exact-ID
control identities/order, statuses, per-stage arithmetic, initialization/cold/warm
arithmetic, response hash presence and byte counts, reconstructable abstention
response hashes, and recorded complete owned-group cleanup. It rejects raw source
fields. Nine synthetic tamper/consistency tests pass.

Actual receipt:
`/workspace/shared/gamma-dot-diagnostics/persistent-recognition-independent-readback-2140.json`.
The input run is `/workspace/shared/gamma-persistent-recognition-timing-20261025-2132`,
freeze `a0ce32d58b0e4c22ac04626569c1a951eb0e10cc0e76575a51c8266a3eb8b256`.

Result: **consistent readback**, 8 description abstentions, zero description
artifact successes, 6 exact-ID artifact successes, zero errors. Thus the diagnostic
measures persistent informal-description **abstention** latency and separate exact-ID
artifact latency, not successful description-to-artifact latency.

Cold initialization plus first query: 5.698 seconds. Second-pass description
requests: 0.601, 0.469, 0.583, 0.557 seconds. OS cache state remains uncontrolled.
These four authored descriptions are not a representative latency benchmark.

This is independent readback consistency—not independent clock attestation,
verification that every encode really occurred, source-byte rehash, candidate
execution/correctness, or recognition qualification. The verifier neither opens
source/model files nor reruns any encoder/candidate.
