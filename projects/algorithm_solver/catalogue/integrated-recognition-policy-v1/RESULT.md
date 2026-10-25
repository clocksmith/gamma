# Integrated fresh-query development replay

Frozen policy `c65-m00` (cosine 0.65, adjusted margin 0, fixed facet weight 0.05) processed all 52 development requests with 52 fresh CPU encodings and all 4,081 rivals. It returned 36/40 correct dual-language artifacts; all 12 controls abstained. There were no wrong decisions, delivery errors, or declared-scope mismatches. Status, identity, and reason matched the frozen cached baseline exactly.

Actual child: 43.6567 s wall, 84.8704 s CPU, peak RSS 3,745,932 KiB; initialization 8.5418 s. Supervisor: 44.6484 s, clean owned-tree verification. No candidate execution. These are measured local full-path costs, not a latency guarantee or clock attestation.

The original 5 GiB headroom preflight failed before claim/model/cohort access (exit 1, 0.0653 s, clean cleanup; available 5,062,508 KiB). That failure is retained. The approved resource-only successor requires 4.75 GiB headroom, 8 GiB address space, 300 CPU seconds and 240 wall seconds, plus a 4.25 GiB sampled conservative summed-RSS watchdog across supervisor and owned processes. Shared pages may be counted more than once; 50 ms sampling permits between-sample overshoot. This is not an instantaneous kernel memory cap. Stop paths kill owned identities immediately and verify/reap under a two-second polling budget.

Confirmation remains sealed. The separate proposal preserves the exact predictor, service and resource hashes and requires root authorization for a one-shot 28-case run. Development success is finite shared-author evidence, not qualification or a population-risk certificate. Private raw reports, query text, vectors, model assets, source payloads and historical draft snapshots are excluded from this public checkpoint.

Timing readback: cold initialization plus first request 9.32255 s; remaining 51 requests p50 0.657728 s / nearest-rank p95 0.835124 s; 36 accepted requests p50 0.680450 s / p95 0.881959 s. One fixed-order authored local persistent cohort only; no network/candidate execution or general goal 1c claim.

Independent readback receipt `53f58d2da0bd5057e9a73d3ffe34bdfd5b5187113ebd5647ff95b9fe32713994` verified all 52 decisions, 72 normative artifact metadata bindings, claim/permit and cleanup. It did not reopen source/model/confirmation or attest the original launch/clock.
