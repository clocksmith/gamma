# A2 Sealed Fresh-Code Evaluation Report: Depth-1 AST Frames (Arm 3) vs Context AST (Arm 2)

## Verdict

- **Preregistered Sealed Verdict (`PREREGISTRATION_DEPTH1.md`):** **`KILL`**
- **Point Estimate (`delta_complete_pct`):** `-0.5324%` (`-17856` complete bits; Arm 3 `3,335,760` vs Arm 2 `3,353,616` bits)
- **Paired Repository-Lineage 95% CI (10,000 resamples, seed=20261127):** `[-0.7055%, -0.3743%]` (pass bar: point `<= -1.0%` AND 95% CI upper `<= -1.0%`)
- **Fidelity Gate:** `corrupt_decodes = 0`, `arm2_byte_exact = True`, `arm3_byte_exact = True` across `426` files / `24` independent JS repository lineages
- **AST Coverage & Charged Raw Fallback:** `419/426` AST-supported, `7` raw-fallback files (`5.47%` of `856,339` normalized bytes; kill threshold `> 25.0%`)
- **Decode Latency Ratio (p95):** Arm 3 `16.318 ms` vs Arm 2 `16.669 ms` (`0.98x`; kill threshold `> 5.0x`)
- **Closed Arm Note:** Recursive Frames (`Arm 4, D_max=3`) remained CLOSED after its `-0.11%` dev FAIL and was NOT run on sealed code.

## Frozen Preregistration Audit (13/13 SHA-256 Verified)

- `score_depth1_sealed.py`: `adf1089ea5262766d3309d24e477ebbd8defad1f163a681a8f5e182b85858f72` (invoked unmodified)
- `frozen/arm2_context_ast.header.a2bits`: `27b98c044a78bf211245530493d0a92bc43732a82099eb29fd1d82d6dc9296c1` (`46,848` header bits)
- `frozen/arm3_depth1_frames.header.a2bits`: `bbc390721469e6323fb2397f2aa02d78d833d7470b9d668904e7569cba4d2151` (`55,320` header bits; `+8,472` bit header tax)
- Disjointness audit: `0` lineage, exact-SHA-256, or whitespace-squeezed-SHA-256 overlaps across `1302` excluded source hashes.

## Complete-Bits & Measured-Work Breakdown

| Arm | Header Bits | Payload Bits | Complete Bits | Encode Wall (s) | Indep. Decode Wall (s) | Decode p95 (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Arm 2 (Context AST, `D=0`) | 46,848 | 3,306,752 | 3,353,616 | 2.191 | 2.220 | 16.669 |
| **Arm 3 (Depth-1 Frames, `D=1`)** | **55,320** | **3,280,424** | **3,335,760** | **3.724** | **2.166** | **16.318** |

- Normalization wall: `0.738 s`, total wall: `11.124 s`, peak RSS: `215.34 MB`.
- Arm 3 exact 8-shift evaluations: `5,793,272`, total Depth-1 frame uses: `2,354`.

## Fresh Sealed JS Repositories (24 Independent Lineages)

| Lineage | Package | Version | Files | Raw Bytes |
| --- | --- | --- | ---: | ---: |
| `repo:jsdom/jsdom` | `jsdom` | `29.1.1` | 22 | 59,958 |
| `repo:microsoft/playwright` | `playwright-core` | `1.58.2` | 16 | 59,794 |
| `repo:capricorn86/happy-dom` | `happy-dom` | `20.10.6` | 14 | 59,977 |
| `repo:Hopding/pdf-lib` | `pdf-lib` | `1.17.1` | 21 | 59,969 |
| `repo:huggingface/transformers.js` | `@huggingface/transformers` | `4.3.2` | 25 | 46,207 |
| `repo:cloudflare/workers-sdk` | `miniflare` | `5.20260925.0-alpha` | 16 | 59,755 |
| `repo:sinclairzx81/typebox` | `@sinclair/typebox` | `0.34.48` | 25 | 57,250 |
| `repo:grpc/grpc-node` | `@grpc/grpc-js` | `1.14.4` | 9 | 59,793 |
| `repo:digitalbazaar/forge` | `node-forge` | `1.4.0` | 17 | 57,531 |
| `repo:toji/gl-matrix` | `gl-matrix` | `2.8.1` | 10 | 59,846 |
| `repo:openai/openai-node` | `openai` | `4.104.0` | 20 | 59,985 |
| `repo:testing-library/user-event` | `@testing-library/user-event` | `14.6.13` | 25 | 57,611 |
| `repo:mochajs/mocha` | `mocha` | `10.8.2` | 15 | 59,875 |
| `repo:csstree/csstree` | `css-tree` | `3.2.1` | 25 | 55,248 |
| `repo:preactjs/preact` | `preact` | `10.29.1` | 15 | 59,942 |
| `repo:chjj/blessed` | `blessed` | `0.1.81` | 14 | 59,943 |
| `repo:vitest-dev/vitest` | `vitest` | `4.1.10` | 25 | 60,000 |
| `repo:open-telemetry/opentelemetry-js` | `@opentelemetry/api` | `1.9.1` | 25 | 27,181 |
| `repo:fb55/entities` | `entities` | `7.0.1` | 14 | 57,678 |
| `repo:ExodusOSS/bytes` | `@exodus/bytes` | `1.16.0` | 20 | 59,856 |
| `repo:connor4312/blake3` | `blake3-wasm` | `2.1.5` | 15 | 59,850 |
| `repo:speed-highlight/core` | `@speed-highlight/core` | `1.2.24` | 18 | 59,989 |
| `repo:kpdecker/jsdiff` | `diff` | `5.2.0` | 9 | 59,075 |
| `repo:websockets/ws` | `ws` | `8.21.0` | 11 | 59,916 |
