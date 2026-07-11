# WRT Wiki Shell v1

`wrt_wiki_shell_v1` reconstructs decoder-visible Wikipedia state at the FX2
WRT byte boundary. It is an observation and residual-research shell around the
existing compressor, not a replacement backend or a constructive score claim.

## Causal Path

```text
decoded FX2/WRT byte prefix
  -> WRT token and dictionary expansion observer
  -> XML entity reconstruction
  -> page/title/prose/ref/url/template/table/list/section FSM
  -> page-scoped title/template/ref/section hashes
  -> shell SSE, retrieval, and router shadow experts
  -> exact arithmetic comparison with the logged FX2 probability
```

The observer loads the same WRT dictionary through a separate read-only table.
Dictionary pretraining is excluded by resetting only observer state after
`Pretrain`; FX2 model state is not reset or changed. Trace rows describe state
available before the current true bit, and all shadow counters update after
that bit.

## Observation Identity

Receipt:
`results/wrt_wiki_shell_v1/observation_identity_1k_entity_final_rss_guard.json`

- Receipt SHA-256: `7b611b7b12e917601b16c64c3e64e29d587fc7fa4e480e2dd57418a8a33f1c3a`
- Observer-off archive SHA-256: `c270e350bd94ff75feb49035396b81379bd75274a5535794f01ad034b64c8f03`
- Observer-on archive SHA-256: `c270e350bd94ff75feb49035396b81379bd75274a5535794f01ad034b64c8f03`
- Both decoded outputs match the input SHA-256
  `0f35cdeee80ba4c570885c34ee901aa579441fb8ba97351568a81bacdfc241fd`.
- Process-tree peak: `4,794,748 KiB`; decimal-limit guard did not fire.
- The first corpus trace row has `wrt_reconstructed_bytes=0`; dictionary
  pretraining no longer contaminates shell history.

This proves observation-mode byte identity and roundtrip at the measured 1K
scope. It does not prove a compression improvement.

## Rich Trace

Receipt:
`results/wrt_wiki_shell_v1/trace_64k_entity_v2/manifest.json`

- Receipt SHA-256: `f20e7cf50e9b4592acaa81e5a5ed4a210bcb850ef42c6a817befa24cb1fa88d0`
- Raw scope: `65,536` bytes
- Exact FX2 residual rows: `301,808`
- WRT token IDs observed: `2,282`
- Dictionary hit widths: one, two, and three bytes
- Page-boundary rows: `168`
- Ref-mode rows: `103,440`; ref-hash states: `8,543`
- Title, prose, URL, list, template, number, section, and their memory hashes
  are nonconstant.
- Table state is unobserved because the first `{|` opener is at raw offset
  `164,724`, outside this trace.

The entity layer is required: refs in this prefix occur as `&lt;ref...&gt;` in
the XML text and were invisible before entity reconstruction.

## Combined Shell SSE

Receipt: `results/wrt_wiki_shell_v1/shell_ledger_64k_v1.json`

- Receipt SHA-256: `61a2b865671b20b28330d18110f775317ad0780e83265fcaebfa72aaaaa0ffcb`
- Models: `33`, spanning token, regime, layout, schema, page memory, and
  regime-router families.
- Exact arithmetic models replayed: `3`.
- Best selection family: `wrt_router_b50000_p32`.
- Exact confirmation saving: `0` bytes.
- Schema confirmation saving: `2` qbits, `0` exact bytes.
- Verdict: `discovery_trace_only`; promotion is disabled at this scope.

Plain shell-keyed residual SSE does not justify a larger or native gate.

## WRT Retrieval Transfer

Receipt:
`results/wrt_wiki_shell_v1/retrieval_shadow_64k_v3_attribution.json`

- Receipt SHA-256: `060b99e459da605be235ef491c04d8a31c63b86caac3d3fafb4b05b8e9870473`
- Prior-WRT-byte alignment: `4,095 / 4,095` exact.
- Routed same-coder result: `-8` bytes overall, `-3` held out.
- Every independently attributed suffix/schema/hash-memory/byte-prior band is
  negative on confirmation.
- The least-negative confirmation band is `sim_schema` at
  `-0.93017578125` qbit-accounted bytes.
- The split-band router has `10` regressing blocks and no positive block.

This retires broad hash buckets and next-byte histograms in their current
shape. It does not retire decoder-built retrieval or schema memory generally.

## Next Eligible Mechanism

Do not enlarge either negative 64K expert. The next implementation must retain
actual page-scoped token sequences rather than only 8-bit hash buckets:

1. decoder-rebuilt tries for titles, template keys, ref/URL fragments, and
   section names;
2. explicit copy distance and match length into prior page/template/ref spans;
3. WRT token-ID sequences as the retrieval alphabet;
4. regime-specific experts with causal cumulative regret and base abstention;
5. held-out same-coder gain minus counted code/table bytes before any native
   compressor gate.

The calibrated requirement remains `10,351.886200` archive bytes at the 10M
proxy for a `12,000`-byte component. Only a mechanism with margin over that
threshold earns native compilation.
