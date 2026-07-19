# Random-Window Novelty Screen V1

This screen tests representation-changing algorithms on deterministic random
`500,000`-byte and `1,000,000`-byte windows drawn across the complete enwik9
corpus. It is Level-1 proxy evidence. It does not change the calibrated score
forecast and does not prove `10.95%`.

## Frozen Contract

- Corpus bytes: `1,000,000,000`
- Corpus SHA-256: `159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`
- Selection: four stratified random windows per scope, `6,000,000` source
  bytes total.
- Confirmation: eight new stratified random windows per scope, `12,000,000`
  source bytes total.
- Selection/confirmation byte-range overlap: `0`.
- Backends: stdlib `bz2` level 9 and `lzma` preset 6.
- Required gross proxy gain: `700` bytes per million under every backend and
  scope.
- Every row requires transform roundtrip, full backend roundtrip, transform
  determinism, and byte-identical second compression.
- Tool: `tools/random_window_novelty_screen.py`.
- Tool SHA-256: `aa74fac4081345673fe4243062a8a34b5736ac1b5db99877a5001070a04aeb93`.

The standard-library backends are intentionally unrelated. Agreement reduces
the chance that a candidate merely exploits one coder's framing or match
heuristic. It does not establish transfer to FX2/cmix.

## Winning Mechanism

`title_echo` builds a deterministic phrase set from the current page title
after that title has already appeared in the decoded stream. The set contains
the exact title, eligible title words, and exact two- and three-word spans. In
the remainder of the same page, an occurrence can be replaced by a two-byte
marker and phrase index. The decoder reconstructs the phrase set from the
decoded title and expands each inline reference.

The mechanism ships no title table, embedding, model weight, page index, or
future label. All route choices are present in the coded stream. Arbitrary
window boundaries, incomplete leading pages, and incomplete trailing pages are
left literal. The transform passed roundtrip and determinism checks on every
measured row.

This is different from the retired `title_ref_columnar_lzma_v1` shape. That
candidate extracted a global title column inside a larger article-geometry and
columnar stack. V1 isolates page-local current-title echoing and compares it
with unchanged input and a matched previous-title control.

## Selection

| Candidate | Minimum gain B/1M | Mean gain B/1M | Decision |
|---|---:|---:|---|
| `title_echo` | 1,588.000 | 1,908.438 | Freeze for confirmation |
| `title_echo_aliases` | 1,504.500 | 2,108.000 | Reject extra complexity |
| `title_echo_aliases_selective` | 1,326.500 | 1,734.188 | Reject extra complexity |
| `title_echo_selective` | 1,190.500 | 1,549.188 | Reject extra complexity |
| `title_echo_multiword` | 926.000 | 1,142.500 | Reject weaker minimum |
| previous-title matched control | -649.500 | -336.250 | Control only |

The simplest exact-title rule has the strongest worst-backend/scope result and
was frozen unchanged. Alias, case, and selection variants did not get access to
confirmation windows.

Other representation families were negative at their weakest backend/scope:

| Family | Best tested minimum gain B/1M | Disposition |
|---|---:|---|
| XML ID delta | -595.500 | Retire this encoding shape |
| Wiki graph MTF | -1,672.000 | Retire tested table sizes |
| Rolling causal phrases | -4,480.500 | Retire tested block sizes |
| ASCII case residual | -29,084.750 | Retire both layouts |

## Untouched Confirmation

| Algorithm | Backend | Scope | Windows | Archive delta | Gain B/1M | Wins/regressions |
|---|---|---:|---:|---:|---:|---:|
| `title_echo` | `bz2_9` | 500,000 | 8 | -7,185 | 1,796.250 | 8/0 |
| `title_echo` | `bz2_9` | 1,000,000 | 8 | -22,162 | 2,770.250 | 8/0 |
| `title_echo` | `lzma_6` | 500,000 | 8 | -6,456 | 1,614.000 | 8/0 |
| `title_echo` | `lzma_6` | 1,000,000 | 8 | -13,388 | 1,673.500 | 8/0 |
| previous-title control | `bz2_9` | 500,000 | 8 | +1,079 | -269.750 | 1/7 |
| previous-title control | `bz2_9` | 1,000,000 | 8 | +1,690 | -211.250 | 2/6 |
| previous-title control | `lzma_6` | 500,000 | 8 | +1,056 | -264.000 | 1/7 |
| previous-title control | `lzma_6` | 1,000,000 | 8 | +2,112 | -264.000 | 0/8 |

The candidate wins all `32` confirmation rows; the matched control regresses in
`28` of `32`. Across selection and confirmation, the frozen candidate wins all
`48` rows. This supports current-title/body alignment rather than generic page
substitution as the source of the proxy gain.

## Economics And Claim Boundary

The conservative confirmation floor is `1,614` gross bytes per million. A
linear `1G` extrapolation is `1,614,000` gross bytes, versus the calibrated
baseline debt of `681,114` bytes. The candidate would need to retain about
`42.2%` of that proxy gain before integration payload. This is useful headroom,
not a score forecast: FX2/WRT may already model much of the same title signal.

The probe source is `42,664` bytes and includes the complete harness, two
backends, controls, and all rejected algorithms. It is not a candidate payload
estimate. No code byte has yet been subtracted from the title-echo gain.

## Native FX2/WRT Transfer

The frozen rule was replayed unchanged on one preselected confirmation window
at each scope through matched native FX2 `-c`/`-d` commands with WRT enabled:

| Scope | Raw archive | Title-echo archive | Delta | Gain B/1M | Roundtrip | Deterministic |
|---:|---:|---:|---:|---:|---|---|
| 500,000 | 96,880 | 97,008 | +128 | -256.000 | yes | yes |
| 1,000,000 | 184,336 | 184,683 | +347 | -347.000 | yes | yes |

All twelve guarded codec phases completed below the decimal `10GB` ceiling;
the largest sampled single-process RSS was `5,783,164 KiB`. The combined
native delta is `+475` archive bytes over `1,500,000` input bytes, or
`-316.667` B/1M. This retires the pre-WRT inline-reference shape before any
integration source cost is charged.

The WRT-only diagnostic makes the result more specific. Title echo shortened
the stored WRT representation by `4,652` bytes at `500K` and `9,014` bytes at
`1M`, with both WRT roundtrips exact. FX2 nevertheless produced larger final
archives. The title/body redundancy is real, but the new marker sequence loses
more predictor context than its shorter representation saves.

The unmodified base commit first received `SIGSEGV` at its periodic PPMD mmap
remap with peak RSS `5,256,596 KiB`. That is preserved as build/correctness
evidence only. The paired results above use one content-hashed research-tree
snapshot with experimental features at default-off values and the address-
preserving remap correction. They do not claim exact public-binary
reproduction.

## Next Mechanism

Do not tune markers, aliases, or occurrence thresholds on these confirmation
ranges. The next eligible construction is `wrt_title_token_automaton_v1`:

1. Preserve the original WRT stream without rewriting it.
2. Rebuild current-title WRT token IDs and literal expansions from decoded
   prefix state.
3. Maintain a bounded page-local prefix/failure automaton over title token
   sequences and expose match length plus predicted next token/byte.
4. Combine that endpoint with base FX2 through causal fixed-point regret and
   abstain when prior loss is non-positive.
5. Use the previous page title as a mechanically matched control on disjoint
   `500K` and `1M` traces.
6. Require more than `700` gross B/1M at every scope before code, then positive
   gain after measured source/state cost and bounded block regressions.

This no-rewrite endpoint tests whether title state improves probability without
destroying the WRT context that the native replay showed to be valuable.

## Follow-On Event-Phase Residual

A separate payload-free residual SSE found a small, distributed signal in WRT
event phase rather than title identity.  Development selected a collision-free
table keyed by current event byte/bit prefix and FX2 confidence, with a coarse
base-confidence backoff.  It saved `17` exact bytes (`34 B/1M`) on the event-
dense offset-`306M` window and the frozen form saved `22` (`44 B/1M`) on the
disjoint offset-`205,537,142` window.  Every one of the `11` measured blocks
was positive.

This is causal raw-FX2 shadow evidence, not endpoint428 evidence.  The observed
rate is below the `57.404 B/1M` remaining endpoint428 debt before integration
source cost, so the unchanged endpoint is retired.  The positive primitive is
retained for one hierarchical event-phase backoff construction that must clear
target economics on disjoint exact traces.

## Receipts

- `results/random_window_novelty_v1/selection.json`
- `results/random_window_novelty_v1/selection.md`
- `results/random_window_novelty_v1/confirmation.json`
- `results/random_window_novelty_v1/confirmation.md`
- `results/random_window_novelty_v1/decision.json`
- `results/random_window_novelty_v1/fx2_native/confirmation-500000-0.json`
- `results/random_window_novelty_v1/fx2_native/confirmation-1000000-0.json`
- `results/random_window_novelty_v1/fx2_native/wrt_transfer_diagnostic.json`
- `results/random_window_novelty_v1/fx2_native/decision.json`
- `results/fx2_reference_residual_v1/wrt-hashed-residual-online-two-window-decision.json`
