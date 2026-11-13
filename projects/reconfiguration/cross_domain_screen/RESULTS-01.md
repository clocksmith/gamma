The fixed 27B exploratory screen completed 24 requests across six tasks. Channel gain and shuffled-context gain each matched base on all six frozen pass/fail outcomes: four passes and two failures. This screen provides no observed gain advantage. It is separate from the 9B WGSL confirmation experiment and does not establish broad transfer.

| Condition | Frozen task passes | Public passes | Wins / losses / ties versus base | Output-cap hits |
| --- | ---: | ---: | --- | ---: |
| Base | 4/6 | 6/6 | — | 0 |
| Channel gain | 4/6 | 6/6 | 0 / 0 / 6 | 0 |
| Shuffled context | 4/6 | 6/6 | 0 / 0 / 6 | 0 |
| Permuted gain | 3/6 | 5/6 | 0 / 1 / 5 | 0 |

All conditions failed both arithmetic tasks and passed both structured-text tasks. Base, channel gain and shuffled context passed both Python tasks. Permuted gain passed `python-runs`; the frozen interpreter rejected its `python-intervals` source before executing cases. Thus the recorded permuted loss is a restricted-interpreter rejection, not demonstrated functional regression.

The rejected source uses `sorted(result, key=lambda x: (x[0], x[1]))`. The interpreter rejects keyword arguments at `ast.Call.keywords` and also excludes `ast.Lambda`. The prompt lists `sorted` as allowed and lists permitted constructs, but does not explicitly forbid keyword arguments or lambdas. A separate CPU diagnostic executed the unchanged sealed function with only its required `min`, `max` and `sorted` builtins: all six frozen public/heldout cases passed, with inputs unchanged. This diagnostic does not alter the frozen scores, outputs or paired table. Its exact source, source hash and case results are in [audit-summary.json](screen-run-01/audit-summary.json).

Arithmetic failures are substantive. Fractions expected `[313, 86, 59]`; every condition returned `[147, 88, 63]`. Congruences expected `[192, 95, 87]`; base returned `[188, 72, 103]`, channel gain `[188, 79, 40]`, shuffled context `[188, 24, 37]`, and permuted gain `[188, 79, 103]`. Channel gain and shuffled context produced source and token IDs identical to base on five tasks; permuted gain did so on four. Every condition has two public-schema passes that fail the full arithmetic oracle.

The model was provisioned `Qwen/Qwen3.8-27B`, revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`, active manifest `e29626a8d3c41c0af8c0dd945d028464dcebfef2413ba85e4f5e8695d5910d06`, mixed Q4_K_M/F16 weights and F32 activation math. The unchanged analytical rule used beta −0.05, clip 1, epsilon 1e−6 and reference A, mapped explicitly to dense MLP layers 62/63. Only the primary base-cache arm ran; there was no adapter comparator or re-prefill arm in this additional screen. Six fixed prompts, four conditions and a 256-token cap were locked before generation. Actual response lengths were 14–128 tokens. Each transformed request used the frozen gain handle, with its first token drawn from base-prefill logits and later tokens using transformed logits.

Three full-model discard/reset diagnostics, one per domain, reproduced all 248,320 baseline logits exactly: relative L2 and maximum absolute difference were zero, and top-1 did not change. This establishes reset behavior for these serial requests, not concurrent full-model isolation.

| Condition | Sum of physical request time | Sum of charged native end-to-end time |
| --- | ---: | ---: |
| Base | 151.175 s | 151.198 s |
| Channel gain | 140.391 s | 162.985 s |
| Shuffled context | 111.790 s | 150.966 s |
| Permuted gain | 102.652 s | 125.742 s |

Charged native time includes each condition's logically required reference/instruction preparation, gain/control work, contract handling and cleanup; shared preparation is physically performed once per task. Physical preparation totaled 40.185 s, including an unused random-z control prepared by the reused helper. Reset diagnostics totaled 10.911 s. Oracle verification took 2.013 s after all outputs were sealed. Cold model load took 79.440 s; execution through scoring took 560.217 s; runtime close took 0.033 s. The exact journal interval from model-load-start to cleanup-end was 639.994 s, 13:01:51.789–13:12:31.783 UTC on 2026-11-13. The first task's four requests, preparation and reset took 29.820 s; its short-response timing did not predict later Python response lengths.

Selected gain storage was 262,144 allocated bytes per transformed request (two 17,408-channel vectors; allocation rounding included). Device GPUBuffer high-water reached 19,051,201,592 bytes across the process. That high-water includes model, cache, pooled temporaries and retained diagnostic/harness storage; it is not incremental gain memory or physical-RAM consumption. Raw ownership, matched-baseline subtraction and device allocation details remain in the receipt.

This ran on Jupiter's AMD Radeon 8060S, Mesa 26.0.3 native WebGPU, while the separate 9B WGSL job continued. The idle 27B provider had been stopped by the owner-authorized root lane. Timings are contended observations, not an isolated speed comparison. Earlier 27B qualification used 256-token prefill chunks; this run supplies actual short-prompt execution evidence for the new split-F32, unchunked gain path, not a long-context qualification. Six tasks and one sample per condition cannot establish general quality retention or improvement.

[Archive manifest](screen-run-01/archive.json) binds the original and compressed hashes of the complete receipt, sealed outputs, raw journal and log. Compression preserved all original bytes; the 123.5 MB receipt is retained as gzip. [Validation](screen-run-01/validation.json) verifies canonical receipt/output identities, the runtime lock, exactly 24 request completions and scoring strictly after the output seal. Runtime lock: `bbff5fe97c1070ec3fb9f60bb9014a5362da11593ac981fd3e617e6c14196b33`; output seal: `10f81e8c2f5be07827f13a30afc0fdff52f2b4aee2152493aaa484c77e79401e`. No source, task, protocol, oracle or model bytes were changed during this evidence collection.
