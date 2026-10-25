# Actual persistent timing diagnostic

This post-freeze result note does not replace frozen source or README versions.
The executed freeze is `a0ce32d58b0e4c22ac04626569c1a951eb0e10cc0e76575a51c8266a3eb8b256`.
Public-safe figures and exact evidence hashes are in [AGGREGATE.json](AGGREGATE.json).

**8 description abstentions; 0 description artifact successes; 6 exact-ID artifact
successes; 0 errors.** Thus this measures description-abstention latency and separate
exact-ID artifact latency—not successful description-to-artifact latency.

- One persistent CPU model, service and complete 4,081-competitor index.
- Four fixed authored descriptions, two passes, fresh encoding on every request.
- Cold process initialization plus first query: **5.698 seconds**.
- Second-pass description requests: **0.469–0.601 seconds**.
- Exact-ID controls 802/875/2406: **0.0369–0.0435 seconds**, six requests total.
- Run: **10.042 seconds wall**, **17.339 seconds CPU**, **3,746,304 KiB peak RSS**.
- Actual materialized dual-language responses were serialized in memory; raw source
  was not published. No candidate was executed. Optional execution remains a
  separately identified diagnostic, not required on every artifact lookup.

Independent readback confirmed count/status/hash-presence/timing arithmetic and
recorded complete owned-group cleanup. It is not independent clock attestation,
model replay, source rehash or candidate correctness evidence. OS cache state was
uncontrolled; four authored descriptions are not a representative latency benchmark.
Recognition and goal 1c remain unqualified. The selected policy's separate historical
recognition result remains 9/40 correct positive accepts.
