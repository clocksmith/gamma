# Portable abstention on saved Qwen development tables

The frozen F16 readout retains the absolute score needed to decide whether to answer. It stores four affine functions of the two layers’ bare answer-marker activations, with the training means and scales folded into their coefficients and intercepts. A separate per-question scale is unnecessary for this signal. Its maximum is a ridge score. It has no probability interpretation.

The optional gate binds the SHA-256 of the exact classifier header, which already pins the coefficient bytes, to the base-model digest, threshold, cutoff rule and hash of the calibration scores grouped by fit table. The caller pins the entire gate. An answer carries the selected code. A fallback carries a null code and leaves the lookup to the caller. The underlying classifier and GPU readback are unchanged.

## Results

The CPU replay read all 2,304 bare marker features across development seeds 1102 and 1103, including 768 uncovered noun queries. It checked every F16 winner against the frozen F64 classifier and every covered correctness judgment against the separately archived discovery records. All matched. Maximum absolute F16 ridge-score deviation from that archive was 0.000467 on seed 1102 and 0.000284 on seed 1103 (rounded up). The unquantized export stayed within 0.00000103.

Each operating point was tested on the same 48 seed-1103 tables, totaling 768 covered questions and 384 uncovered. Every F16 accept/fallback decision agreed with the corresponding full-precision decision.

| Gate | Covered accepted | Correct among these | Uncovered accepted | Wrong direct | Unnecessary fallbacks | All fallbacks |
|---|---:|---:|---:|---:|---:|---:|
| Cross-seed, calibrated for 5% uncovered acceptance | 512/768 | 511/512 | 10/384 | 11 | 236 | 630 |
| Two folds of whole tables, calibrated for 35% lookups | 678/768 | 673/678 | 55/384 | 60 | 74 | 419 |

The cross-seed cutoff uses only the 384 uncovered scores on seed 1102. Rank 20 in descending order reproduces the stored double 0.6485258948040804 exactly. Strictly greater scores answer. One calibration row tied. Eight evaluation tables had a false accept, at most two of eight uncovered questions on any table. The gate adds 439 serialized bytes to a 57,857–57,867 byte classifier. Its coefficients alone occupy 57,352 bytes.

The lookup-rate test follows the original Python rule. Sort seed-1103 table IDs lexicographically, alternate into two halves, set the cutoff from the pooled score distribution of 24 fit tables, then apply it to the opposite 24. Accept equality. The cutoffs were 0.4104740705517568 and 0.46237911389321146. Each had one calibration tie. Neither evaluation rule encountered an exact tie on a held-out question. The regression test exercises equality explicitly. At this operating point the original decoder and nearest-neighbor controls produced 160 and 210 wrong direct answers respectively. Those control counts and table-bootstrap uncertainty are in the [earlier float replay](https://github.com/clocksmith/gamma/blob/ef2df0348e5d0973703369d6ca3fef00fcbc7c73/projects/reconfiguration/query_swiglu_fastweight_v5/lookup_gate_reproduction_1103.json).

The example gate in this directory is bound to the exact table used in the previous raw-text two-host readout. For that table, both a covered question and the uncovered noun “shirt” produce the ungated class “east.” Their maxima are 0.714705 and 0.163382. Only the covered one clears the strict cutoff. The replay also loaded the existing two-host raw-text score receipt through the new gate. That one previously observed covered result cleared the cutoff. No new model run, network transfer, retrieval, latency measurement or MiniCPM data was involved. An uncovered query can still clear either cutoff.

## Reproduce

From the parent directory, supply the existing Qwen development discovery directory with both dumps and their float reports, the frozen classifier export directory, and an unused output directory. The script checks the source and coefficient identities, writes a bound gate for each held-out classifier and saves results per table. The fit-score digest covers UTF-8 compact JSON plus newline of sorted table IDs and their score vectors in original question order.

```sh
node --js-float16array readout_gate_replay.mjs DISCOVERY CLASSIFIER_EXPORT NEW_OUTPUT
node --test readout_gate.test.mjs
```

For the existing live readout runner, add the selected gate file’s SHA-256 to the fixture as `gateSha256`, then append the gate file to its normal command. Each fixture task can specify `expectedAction` as `answer` or `lookup`. A gated fixture rejects a missing or mismatched policy before model loading.
