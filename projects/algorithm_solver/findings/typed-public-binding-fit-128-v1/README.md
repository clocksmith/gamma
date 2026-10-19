# Explicit public fallback binding: bounded hypothesis exhausted

The candidate correctly binds the public declaration “If there is no such earliest
time, return -1” to the acquaintance graph's return-only accumulator, replacing
its predicted initial 1. It then freezes that literal and uses the same model
logits to search other literals. Nevertheless, the ten-fit comparison remains
**8/10 correct versus 8/10 guard control**, with zero wrong acceptances, zero
lost correct answers and zero infrastructure failures. Structural control is 4/10.
The new candidate is **not selected or promoted**. No fresh-inference rerun was
performed for a candidate with no semantic gain.

## Mechanism and bounded result

The opt-in module recognizes one complete absent-result clause before examples.
It requires a single integer initializer for the final return binding, no body
reads of that binding, and only conditional subsequent assignments. Multiple
literal-return declarations, quoted clauses, example-only instructions, missing
writes and computational/control uses disable the binding. It copies the typed
graph and binds exactly one literal from explicit query text; no target value
or independent test supplies the replacement.

This is a new deterministic public binding followed by at most two model-bit
flips, not a claim that the earlier two-total-bit candidate changed three bits.
The complete route retains four extra public executions and 0.25 seconds inside
the existing two-second budget. Original logits are checked against original
captured bits; only the declared bound slot may differ, and search cannot undo
that slot. All nonliteral structure is unchanged. Candidate code is returned
only after real public verification. Default routes remain unchanged.

For lcd:1101 the four attempted changes were endpoint index, returned tuple-field
index, decrement amount, and endpoint plus returned-field index. They all failed
public checks. Post-score qualified-label analysis identifies the needed remaining
pair as endpoint slot 23 bit 2 and component-completion slot 34 bit 1. It ranks **10th**
by the unchanged model-margin order, beyond the four-execution limit. Slot 39,
ranked ahead of the completion count, is the returned timestamp-field index;
changing it does not fix connectivity. No budget or ordering was changed after
this result. The seven-bit lcd:1489 failure also remains unsolved.

Thirty public decisions were sealed before original independent test sets were
loaded and their qualification hashes checked. The run completed in 4.432 seconds
under two CPU threads, 2 GiB and a 120-second cap. Captured inference is excluded;
this is consumed-fit hypothesis evidence, not release, latency or generalization
qualification. The prior selected 8/10 capture and 7/10 fresh results remain intact.

Software checks passed: 59 focused tests plus 9 subtests, including real sandbox
verification of both a bound fallback and separately repaired literal, original
logit integrity, frozen-slot preservation and disabled ambiguous bindings.
Changed Python compiled and imported. No vocabulary, training, protected access,
new dependency, service intervention or public push occurred.

## Dominant runtime cost, inspected without another run

[Attribution](runtime-attribution.json) reads sealed phases from
`typed-guard-fresh-fit-128-v1`. Across ten warm candidate routes, query embedding
accounts for 16.136 of 16.607 summed seconds (**97.17%**). Prediction totals 0.0281 s
and retrieval 0.00062 s. These are summed per-query warm phase measurements,
not total run wall time or a causal host-contention claim. Cold setup, fit-memory
embedding and independent scoring remain separate. The unchanged fresh p95 is
3.023 seconds against the 2-second gate. Optimizing the small graph predictor is
not supported as the primary runtime intervention by these measurements.

The next composition hypothesis must address the DSU component-count invariant
and endpoint/weight field roles with a separately frozen rule and adversarial
checks. Merely widening model-bit enumeration is not the measured candidate.
For lcd:1489, seven coupled literal errors remain outside the present model
repair support. No training is authorized by this negative result.

Evidence: [manifest](candidate.json), [summary](summary.json),
[decision seal](decisions-seal.json), [driver](run_binding.py).
Raw graphs, traces and independent scores remain local under
`runs/typed-public-binding-fit-128-v1`.
