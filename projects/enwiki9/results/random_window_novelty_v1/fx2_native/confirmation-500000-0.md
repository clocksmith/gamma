# Random-Window FX2 Title-Echo Gate

- Window: `confirmation-500000-0`
- Offset: `70252800`
- Scope bytes: `500000`
- Status: `complete`
- FX2 source commit: `04c5806f99b9b0fa8572be8c8063b4324ec405de`
- FX2 binary SHA-256: `4d9f0df9904453635c213a158da1bdf387763dc7c4088e3d61681598c97fc2df`
- Backend path: native FX2 `-c`/`-d` with WRT dictionary preprocessing.
- Claim boundary: an arbitrary-window target-substrate result is not an official prefix score or a 10.95% proof.

## Result

- Raw archive: `96880` bytes
- Title-echo archive: `97008` bytes
- Candidate delta: `+128` bytes
- Gross gain: `-256.000` B/1M
- Transform size delta: `-12366` bytes
- Raw roundtrip: `true`
- Candidate roundtrip: `true`
- Raw deterministic archive: `true`
- Candidate deterministic archive: `true`
- Verdict: `negative_native_transfer`

## Guarded Phases

| Phase | Return | Peak single RSS KiB | Guard status |
|---|---:|---:|---|
| `identity_compress_a` | 0 | 5727464 | `complete` |
| `candidate_compress_a` | 0 | 5728728 | `complete` |
| `identity_decompress` | 0 | 5727140 | `complete` |
| `candidate_decompress` | 0 | 5728196 | `complete` |
| `identity_compress_b` | 0 | 5727776 | `complete` |
| `candidate_compress_b` | 0 | 5728460 | `complete` |
