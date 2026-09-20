# Joint data/model training for native FX2

The primary attack is a competitive **single-stream** compressor whose compact
predictor is jointly optimized for data and packed-weight cost. Test causal
metadata inside that predictor. The target remains 96,000,000 complete bytes,
with 95,000,000 as stretch; Gamma's verified full-corpus score remains unknown.

Preserve the [census and split result](xml_history_census_20260919.md).
J=148,014 loses to B=142,449 and P=86,703. Its 61,311-byte deficit against P
contains 39,627 additional framing bytes and 21,684 additional payload bytes.
J beating shifted S by 473 bytes does not establish a useful cross-stream
predictor against B. Raw category shares and available references are not paid
compression savings.

## Comparison and decision authority

| Checkpoint | Change | Required comparison |
| --- | --- | --- |
| P | Authenticated existing FX2 model and packing | Exact competitive baseline |
| E | Retrain the existing hidden representation with weight-description cost | Final archive and actual packed bytes versus P |
| M | Same training budget with causal metadata inside the predictor | Paid gain versus E, not just P |
| S | Same capacity and training budget with already decoded wrong donors | Attribution control for M |
| K | Zero metadata contribution | Exact E behavior, including finite archives |

Keep frontend, statistical bank, final mixer, arithmetic coder and native build
profile fixed initially. Training loss is a surrogate; every selected checkpoint
needs fresh native state replay, exact independent inverse and deterministic
raw-input repeat. Do not certify a changed trajectory using frozen parent counts.
Metadata visibility follows complete WRT inverse emissions. No future raw-file
indexing, transmitted donor ledger, separate stream or separate termination.
Share the existing embeddings before adding another complete model.

The acceptance deliverable is trained weights plus actual 250KB and 1MB native
archives, packed model bytes/copies, source/executable/options differences, and
encode/decode time and peak memory. Preserve all checkpoints and failed runs.
Do not charge the full fixed model once per small sample or extrapolate sampled
gains into a full-corpus score. A separate frozen confirmation precedes 10MB,
100MB and any full-corpus execution.

For the stated two-copy package layout, disjoint components satisfy
`S = A + 2W + C + H`. Embedded weights cannot also be counted inside A.
The exact improvement is `delta A + 2 delta W + delta C + delta H`.
Neither the copy count nor package closure may be inferred from a workspace.

Metadata reconstructed from full history adds no information conditional on
that full history. Its potential value is better access for a bounded model.
Price fixed opportunities against the parent's actual residual cost and retain
common-word versus title/entity attribution. Do not infer achievable savings
from the XML percentage or invoke a reconstruction induction as a size proof.

## Implemented development substrate

[Reference adaptation](../src/gamma_enwiki9/adapters/fx2_training_reference.py)
authenticates six upstream Python sources, derives an isolated package, replaces
FLA with the upstream FP32 reference kernels and selects PyTorch SDPA. Shape
annotations are lowered to Tensor; no fake FLA/jaxtyping packages are installed.
The exporter config's missing `query_key_norm_gain=False` is supplied from the
upstream save_outputs recipe. Strict loading retains all 5,923,228 tensor
elements. Historical and external source files stay unchanged.

[Weight objective/export](../src/gamma_enwiki9/adapters/fx2_weight_training.py)
uses exact signed half-even 15-level quantization and BF16 scales for forward
histogram counts, with interpolated counts for gradients. Its smoothed global
histogram rate is a differentiable **surrogate**, excluding scale, raw tensor,
header and adaptive-coder costs. The actual packed file prices those terms.
Full-population normalization and model copy count must be declared explicitly;
the minibatch size is not the fixed-model amortization denominator.

CPU export preserves the parent's authenticated RoPE tables and native config;
unexpected tensor names/shapes/dtypes fail closed. All 434 exported parent
tensors matched the existing native container in the local preflight. This
establishes weight-format compatibility, not FP32/fused-kernel prediction
identity or an archive gain. Export of additional metadata parameters needs its
own explicit native tensor contract.

## Runtime and remaining execution gates

On this host, system Python has torch 2.11.0+cu130 and numpy but no usable GPU.
The separate ROCm environment sees one device but real compute fails: normal
mode reports `invalid device function`; the prescribed gfx11 override reports
`no kernel image is available`. Do not launch GPU training in that environment.
CPU reference forward/backward on eight synthetic tokens succeeds with finite
gradients through 429 parameter tensors. These are synthetic implementation
checks. The CPU P/E development run below now supplies an actual trained checkpoint and native archives.

No new dependencies or model downloads are needed for the implemented CPU
preflight. The PyTorch reference profile differs from the original fused CUDA
trainer and must be named in every future training receipt.

Before corpus optimization, freeze an adaptive experiment with the exact raw
and WRT populations, PPMD rows, reset/warmup alignment, training steps, optimizer,
regularization normalization, seed, metadata interface, controls, resource caps
and stop rule. Publish ownership through the lab. The parent exposes probability
and token extraction flags; article-boundary extraction is restricted to its
full enwik9 preprocessing mode, so a bounded `-c` run needs its own verified
reset-coordinate capture. Do not silently feed misaligned priors or artificial
article boundaries into training.

## Executed P/E development

The [frozen P/E retry](../operations/adaptive/experiments/fx2_entropy_train250k_q0_v2.json)
completed under the lab as `20260919T235340Z_dfd8692458`.
The [comparison](../results/fx2_entropy_train250k_q0_v2/comparison.json) records:

| Component | P | E | P minus E |
| --- | ---: | ---: | ---: |
| Native 250KB archive | 33,429 | 39,639 | -6,210 |
| Packed weights per copy | 2,930,652 | 2,903,502 | 27,150 |
| Sample plus two copies of weights | 5,894,733 | 5,846,643 | 48,090 |

All 16 updates completed. The [training receipt](../results/fx2_entropy_train250k_q0_v2/native/E/training.json)
records 2,048 loss-token exposures, 429 changed participating parameter tensors
and 377 changed native exported tensors. Native inverse and raw-input repeat
pass. Actual capture contains 151,210 modeled tokens, 98 first steps and 97
piece-ending rows, independently matched to the retained WRT representation.

The smaller model comes with a worse payload on this prefix. The positive
sample-plus-model difference does **not** establish a full-corpus improvement.
The [reflection](../operations/adaptive/reflections/20260919T235340Z_dfd8692458.json)
holds E and records zero objective credit. No complete self-extracting delivery
or full-corpus score has been constructed.

The [v1 failure](../operations/adaptive/reflections/20260919T234053Z_f45f995b34.json)
remains preserved. PPMD requests a 14,680,064,000-byte sparse mapping, which cannot
fit a 10GB virtual-address limit. V2 separates its 32GiB address allowance from
the unchanged 9,999,998,976-byte resident cgroup and zero swap. A separately
provisioned Linux fixture verifies a 256MiB mapping under a 64MiB resident cap.
This fixes execution admission; it grants no resource qualification.

Terminal reflection also exposed a framework-history defect after that fix:
current framework bytes were being required for an old terminal's input check.
The corrected terminal-only interpretation resolves exact current or retained
CAS input identities and reconstructs original Python import geometry. New
launch validation still requires current bindings. This is not execution of the
original validator and does not rewrite any historical digest.

## Frozen metadata comparison

The [title experiment](../operations/adaptive/experiments/fx2_title_train250k_q0_v1.json)
uses a bounded bag of the first 128 modeled tokens from a completed title.
Metadata becomes available only after complete WRT inverse emissions and the
closing title tag. Inside text, M uses the current completed title and S the
previous completed title, with the same prefix count and capacity. These donors
can be related; this is a causal wrong-donor control, not random information.
Token order is deliberately discarded. This does not implement general XML or
entity-reference modeling.

The model shares its existing normalized token embeddings. A counted 192-value
FP32 gain vector injects their mean before block zero; M/S retrain all original
parameters and gains from P with the same windows, seed and 16-update budget as
E. Mode and gain are explicit packed tensors. K adds zero gains to E and must
preserve E's native archive exactly. Synthetic tests verify zero behavior,
nonzero gain gradients, future-feature causality, matched capacity, partial WRT
emissions and deterministic introduced state. Native source builds successfully.

The [completed title comparison](../results/fx2_title_train250k_q0_v1/comparison.json)
records P33,429, E/K39,639, M39,768 and S39,349 archive bytes. All192 added gains
train in each M/S model;384 unique loss rows have active title features. M packs
to2,904,379 bytes and S to2,904,419. M therefore loses129 archive bytes to E and
419 to the wrong-title control, while adding877 packed bytes per copy over E.
The adapted executable adds20,480 bytes; the same deterministic source-only ZIP
representation adds6,234 bytes. The declared option-byte delta is zero: metadata mode and gains are in the
counted weights. These are separately priced alternatives, not an assembled
submission package. Even before code cost, M loses1,883 bytes in
the local archive-plus-two-copy-weight comparison against E.

K/M/S independent inverses, raw repeats, introduced-state traces, causal feature
rows and raw WRT witnesses match exactly. The existing terminal recorder checked
and published five [arm receipts](../results/fx2_title_train250k_q0_v1/terminal-index.json).
P/E archive identity was freshly checked here; their independent inverse/repeat
comes from the earlier P/E job, so the new P/E arm receipts leave those fresh-job
fields null. The [reflection](../operations/adaptive/reflections/20260920T001912Z_ad57d1ee71.json)
rejects this local title configuration as a gain. It does not reject general
metadata or full-model retraining.

The [frozen1MB audit](../operations/adaptive/experiments/fx2_joint_replay1m_q0_v1.json)
replays every trained model without fitting, selection or population rescue.
It uses the already retained raw interval713,000,000..713,999,999, with653,296
modeled tokens and an exact131,238-byte P baseline. This is outside the current
training windows and was exposed to earlier research. P/E/M/S receive fresh
encode/decode/repeat; K receives an encode-equality check, retaining its250KB
inverse/repeat evidence. Per-phase maximum process RSS and aggregate job cgroup
peak are distinct observations. The audit does not promote the unfavorable
local model or authorize10MB,100MB or full-corpus execution.

## Completed 1MB replay

The [closed comparison](../results/fx2_joint_replay1m_q0_v1/comparison.json) supplies
fresh native archives without any additional fitting. All P/E/M/S inverses and
raw-input repeats pass. K encodes identically to E; its inverse/repeat evidence
remains the separately recorded 250KB check. The native rebuild and P archive
match their exact retained baselines. Introduced metadata state, features and
raw reconstruction agree across all seven captured phases.

| Arm | 250KB archive | 1MB archive | Packed model per copy |
| --- | ---: | ---: | ---: |
| P | 33,429 | 131,238 | 2,930,652 |
| E | 39,639 | 154,176 | 2,903,502 |
| K | 39,639 | 154,176 | 2,903,607 |
| M | 39,768 | 154,695 | 2,904,379 |
| S | 39,349 | 153,231 | 2,904,419 |

M loses 519 archive bytes to E and 1,464 to S. With two copies of its additional
877 model bytes, it loses 2,273 bytes before code; the inherited two-executable
planning comparison loses 43,233 bytes. The [validated reflection](../operations/adaptive/reflections/20260920T003339Z_270e77a7ca.json)
retires this fixed title configuration. It does not reject metadata in general.

E saves 27,150 packed bytes per copy and loses 22,938 payload bytes here. The
31,362-byte difference for this sample plus two model copies is component
arithmetic, not a full-corpus gain. No complete delivery or full-corpus score
has been measured; the target remains 96M, stretch 95M, with zero earned credit.

| Arm | Encode seconds | Decode seconds | Encode maximum process RSS (KiB) |
| --- | ---: | ---: | ---: |
| P | 127.84 | 127.49 | 5,809,336 |
| E | 138.64 | 143.91 | 5,809,332 |
| K | 147.02 | not repeated | 5,810,676 |
| M | 154.17 | 146.62 | 5,810,680 |
| S | 137.27 | 138.63 | 5,810,672 |

Timings are shared-host diagnostics. The outer guard closed with return code
zero, 6,730,424,320 bytes of aggregate cgroup peak memory and completed cleanup.
This differs from the per-process RSS observations above and grants no contest
resource qualification. The existing recorder published five [arm receipts](../results/fx2_joint_replay1m_q0_v1/terminal-index.json).
All 724 files across the three successful experiment manifests were rehashed;
all six retained gzip witnesses reconstruct their recorded logical identities.
No 10MB, 100MB or full-corpus run was launched.

The [final handoff receipt](../operations/provenance/fx2_joint_training_final_20260919.json)
binds validation, runtime limitations, component boundaries and the next
experiment prerequisite to the retained evidence.

## Measured CPU/native numerical gap

The [synthetic reference diagnostic](../operations/evidence/fx2_reference_synthetic_20260919/report.json)
feeds tokens 0 through 7, a constant binary16 prior and one cold reset into both
implementations. P's first five outputs agree within 0.000006 in absolute
post-softcap logit value. Later differences reach 0.768214; E reaches 0.325458.
These are observations for eight synthetic tokens, not universal error bounds.
Native E and zero-title K remain bitwise identical on this fixture.

The [quantization diagnostic](../operations/evidence/fx2_quantization_synthetic_20260919/report.json)
localizes P's first observed block divergence to block 3's MLP down-projection
input at token index 5, coordinate 634. All nine inspected quantization stages
in that block agree except this one bin: native's scaled value is
3.4999985694885254 and rounds to 3, while the CPU reference's value is exactly
3.5 and rounds to 4. This demonstrates a rounding discontinuity between the
native folded integer computation and the CPU fake-quantized FP32 computation.
It does not establish how much of the measured archive regression it causes or
exclude additional numerical differences elsewhere.

Both diagnostics have retained inputs, source adaptation identities, binary
observations and explicit synthetic replay scripts under `tests/`. They do not
read corpus data or update parameters. The training profile already declares
native prediction parity unestablished; the new evidence measures that gap.
The trained archives remain valid observations of that profile. Before another
training comparison, establish a native-aligned forward objective or explicitly
measure and control its mismatch. Preserve these checkpoints and receipts;
do not reinterpret surrogate loss as final-coder improvement.

## External evidence

[Mahoney's September 2026 entry](https://mattmahoney.net/dc/text.html#0960)
reproduces Zmix's author description of retraining with compressed-weight cost,
packing and implementation changes. Zmix remains an external benchmark here,
not source-audited or reproduced by Gamma; FX2 mutations inherit none of its
reported gains. See the [dated frontier](../operations/provenance/competitive_frontier_20260919.json).
[Entropy-penalized parameter compression](https://arxiv.org/abs/1906.06624) is
prior work, not an enwik9 size theorem. A prize witness still needs the exact
full-corpus package and the applicable independent eligibility checks.
