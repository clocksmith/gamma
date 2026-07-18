# Random-Window FX2 Title-Echo Gate

- Window: `confirmation-500000-0`
- Offset: `70252800`
- Scope bytes: `500000`
- Status: `failed`
- FX2 source commit: `04c5806f99b9b0fa8572be8c8063b4324ec405de`
- FX2 binary SHA-256: `171919c514b8d5a366576434a307ada2a3aa067c7c1f02a91394f6309ef25e5b`
- Backend path: native FX2 `-c`/`-d` with WRT dictionary preprocessing.
- Claim boundary: an arbitrary-window target-substrate result is not an official prefix score or a 10.95% proof.

## Failure

`phase identity_compress_a returned 245`

## Guarded Phases

| Phase | Return | Peak single RSS KiB | Guard status |
|---|---:|---:|---|
| `identity_compress_a` | 245 | 5256596 | `complete` |
