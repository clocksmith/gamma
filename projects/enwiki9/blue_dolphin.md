# blue_dolphin — status and next steps

Build-out of the blue_dolphin namespace, what's measured, what's broken and
fixed, what the hardware allows, and what to do next.

## Programs in the namespace

| program | layers | back-end | program.py size | status |
| --- | --- | --- | --- | --- |
| `blue_dolphin_markup_opcode_cmix_v1` | 38-token markup opcode | cmix (via cmix_wrapped import) | 2,845 B | **redundant**: same idea as `purple_parrot_apex_v1` but score-dishonest (cmix binary not inlined) |
| `blue_dolphin_mediawiki_inline_v1` | 6-state typed inline channels | lzma -e9 | 3,688 B | **smoke PASS** all 4 tiers; full corpus pending |
| `blue_dolphin_tree_macro_v1` | parameterized tree macros over parsed templates (RePair-class admission) | lzma -e9 | 9,893 B (after fix) | **smoke PASS** after bug fix; full corpus pending |
| `blue_dolphin_master_ultimate_v1` | L1 opcodes + L2 channels + L3 tree macros + L4 sidecar features (extracted, not yet fed) + L5 cmix + L6 SSM stub | cmix | 21,604 B | 1 KB roundtrip OK; bundled architecture; **needs layer ablation before scope tests** |
| `blue_dolphin_apex_v1` | markup opcode + cmix | cmix (via cmix_wrapped import) | 3,212 B | 1 KB roundtrip OK; **superseded by `purple_parrot_apex_v1`** (inlined cmix, base85-gzip, code-golfed to 1,493 B glue + score-honest 504 KB total) |

## Bugs found and fixed

**OP_LIT length-counting bug** (recurring pattern across this repo's typed-stream programs):
encoder writes `_varint(len(payload))` — the *original* byte count — then emits *escaped* bytes that can be longer than the original. Decoder uses `end = pos + length` with the original count and runs past the actual literal block, mis-parsing escape bytes as new opcodes. This is the same class as `title_table_v1`'s `bad op 0x6` failure.

Fixed in:
- `blue_dolphin_tree_macro_v1` — `bad opcode 136` on /dev/urandom, now PASS
- `blue_dolphin_master_ultimate_v1` — same pattern, fixed proactively

Fix pattern: track decoded byte count, not stream byte count.

```python
length, pos = _read_varint(stream, pos)
decoded = 0
while decoded < length:
    b = stream[pos]
    if b == ESC and stream[pos + 1] == LIT_ESC:
        out.append(ESC); pos += 2
    else:
        out.append(b); pos += 1
    decoded += 1
```

This pattern should be written down once, shared via a helper, and used by every typed-stream program that needs ESC-byte escape. **Action: extract to `lib/typed_stream.py`** so it can't be re-bugged independently in each new program.

## Hardware reality (cmix wall clock on this box)

| scope | observed wall clock | category |
| --- | --- | --- |
| 1 KB cmix | ~2.25 sec | smoke |
| 1 MB cmix | **>10 min** (timeout fired, not completed) | committed run |
| 10 MB cmix | **>30 min** (timeout fired, not completed) | overnight |
| 100 MB cmix | likely **multi-hour** | overnight + large window |
| 1 GB cmix | likely **multi-day** | certification only |

Implication: **cmix is not the iteration substrate on this machine.** Even 1 MB cmix is >10 min, well outside an iteration loop. The cmix-based blue_dolphin programs (apex, master_ultimate, markup_opcode_cmix) are not benchable on this hardware in iteration time.

The realistic separation:
- **Iteration**: lzma-class only. seconds per run. all preprocessor logic validated here.
- **cmix bench**: queued as committed runs. Overnight or longer. Substrate-question gating only after lzma iteration validates a feature direction.
- **Certification**: full 10⁹ on cmix. Multi-day. One-shot per architectural decision.

## The 10% (sub-100 MB) gap

100 MB on enwik9 is not reachable in pure-Python lzma class. The lzma plateau is ~190 MB (xz_lzma2_1g already at 197.8 MB). Closing the 90 MB gap to 10% requires:

1. **cmix substrate** — gets to ~110 MB (11%) with markup opcode preprocessing. The Python wrapper is `purple_parrot_apex_v1`. Can't iterate on this hardware.
2. **C++ cmix fork with sidecar context families** — adds the 10 sidecar features (computed by `compute_sidecar_features()` in `master_ultimate_v1`) as additional mixer inputs. Predicted ~99–105 MB. Multi-month engineering.
3. **Integer-quantized SSM as a mixer family** (Phase 6 / sub-100 MB bet) — predicted 94–99 MB if the determinism contract holds. Pinned design from prior turns: N=16 subsampled updates, 32-segment integer LUT softmax, fixed-PRNG-seeded weights, hidden state zeroed, truncated BPTT K=64, byte-level distribution.

None of (2) or (3) is single-session Python work. The blue_dolphin Python ceiling on this hardware is the apex program at cmix-class compression, ~110-113 MB full corpus.

## Next steps per program

### `blue_dolphin_markup_opcode_cmix_v1`
**Retire.** The score-honest version is `purple_parrot_apex_v1`. No reason to keep this in the registry — it under-counts by importing `cmix_wrapped`'s binary.

### `blue_dolphin_mediawiki_inline_v1`
**Run on full 10⁹ via lzma** — overnight or cloud host. Compare against `baseline_lzma` (211.8 MB) and `schema_lzma_v1` (209.9 MB). The hypothesis to test: *do inline state-transition markers (avoiding stream-split context loss) help an lzma back-end, or does the marker overhead exceed the typed-context benefit?* Predicted: probably loses to schema_lzma_v1 because lzma can't exploit the markers as semantic signals (lzma is dictionary-based, not context-mixing). If it *wins*, that's a meaningful Track-A signal for cmix re-test.

Specific bench command: `python3 lib/driver.py blue_dolphin_mediawiki_inline_v1` (full corpus default).

### `blue_dolphin_tree_macro_v1`
**Run on 10 MB and 100 MB lzma** to see if tree-macro admission earns its bookkeeping at scope. The fixed-span macro miner (`ast_macro_lzma_v1`) failed at +0.89% to +4.69% loss; this *should* do better because (a) it works on parsed templates not byte spans, (b) frequency floor is f≥3 with a true savings test, (c) arguments stay literal. If it loses by a similar margin, the parsed-template-macro idea is empirically retired.

After the lzma full corpus run: if it wins or is close (<1% loss), queue cmix at 100 MB overnight as the substrate test.

### `blue_dolphin_master_ultimate_v1`
**Defer until layer ablations land.** This program bundles 6 layers. Pragmatic next step: run *each layer in isolation* on lzma full corpus before benchmarking the bundle. Specifically:
- Layer 1 (markup opcode) only — already exists as `ast_opcode_lzma_v1`
- Layer 2 (typed channels) only — `blue_dolphin_mediawiki_inline_v1`
- Layer 3 (tree macros) only — `blue_dolphin_tree_macro_v1`
- L1+L2 — does not exist; would need a new program
- L1+L2+L3 — exists implicitly in master_ultimate (with cmix backend tacked on)

Without isolated layer measurements, master_ultimate's S can't be attributed to any single layer. The pragmatic move is to skip it until the per-layer numbers exist.

### `blue_dolphin_apex_v1`
**Retire.** Same architecture as `purple_parrot_apex_v1`. Less score-honest (imports cmix_wrapped instead of inlining). No reason to bench separately; results would be misleading by the underrepresented program_size.

## What to bench next (priority order)

The tractable next bench actions on this hardware:

1. **`blue_dolphin_mediawiki_inline_v1` full corpus, lzma.** ~30 min. Tells us whether inline-marker channels beat raw lzma + whether they beat schema_lzma_v1. **Highest info-per-time** in the iteration tier.

2. **`blue_dolphin_tree_macro_v1` full corpus, lzma.** ~30 min. Tells us whether the parsed-template macro idea earns bookkeeping at scale. Validates Phase 5 of the locked plan.

3. **Compose `blue_dolphin_mediawiki_inline_v1` + markup opcode + lzma**. New program (`blue_dolphin_inline_opcode_lzma_v1`?). Tests whether two layers compose positively under lzma. ~2 KB program; ~30 min full corpus.

4. **`purple_parrot_apex_v1` cmix at 1 MB**. Already queued by user; ~10+ min. Tells us the substrate question (does markup opcode help cmix or fight it).

The cmix-substrate-question programs (apex variants, markup_opcode_cmix) should not run on this machine — they belong to the overnight queue or the cloud routine.

## Cross-cutting infrastructure

1. **Extract `lib/typed_stream.py`** for the OP_LIT escape-aware literal encoding/decoding. The bug fixed three times in this session is one helper away from never recurring.

2. **Add scope-aware program_size sanity to `lib/driver.py`.** Marginal-byte break-even is `8 × |program| / n` bits/byte. The driver should report this number alongside b/B so contributors can see whether their preprocessor's archive Δ exceeds its program-size cost at the scope they ran at.

3. **`lib/smoke.py` needs a cmix-aware path.** The current 5-tier smoke runs 100 KB through cmix at tier 2, which times out on this hardware. A `--cmix-class` mode that drops tier 2 to 10 KB and tier 5 to 10 KB-1 MB would let cmix-using programs smoke in <2 minutes.

4. **Move SSM-context-family work to a cloud branch.** The integer-quantized Mamba-class SSM is the sub-100 MB bet. It's not buildable on this machine in iteration time. Either offload to a cloud worker, or accept that this is the project's certification-tier work, not iteration-tier.

## Honest closing

The blue_dolphin namespace was an architectural exercise — bundle every winning idea into one program (`master_ultimate`), then test. The empirical lesson is that bundling without isolated Δ measurement is unverifiable; the marginal-byte-break-even math punishes elaborate architecture at iteration scope; and cmix wall clock on this hardware makes the cmix-substrate question only answerable on overnight or cloud runs.

The shippable program from this namespace is *not* `master_ultimate`. It's the equivalent of `purple_parrot_apex_v1` (markup opcode + inlined cmix). The blue_dolphin work that has measurable forward value is the lzma-class typed-stream variants — `mediawiki_inline_v1` and `tree_macro_v1` — both of which now smoke clean and need full-corpus runs to settle.

**Pinned next action**: queue `blue_dolphin_mediawiki_inline_v1` and `blue_dolphin_tree_macro_v1` for full corpus lzma runs. Both ~30 min. Numbers from those settle Phase 4 (typed inline channels) and Phase 5 (parsed-template macros) for this repo without spending any cmix time.
