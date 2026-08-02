# MÖBIUS-2 residual-directed concept discovery

Status: zero-credit discovery protocol; no compression candidate or promotion
claim exists yet.

## Motivation

The exact state-preserving bypass mechanism remains valid, but the frozen
single-prototype, ordered surface-template, lexical-frame, and whole-clause
semantic-role populations did not expose target-scale headroom. The next
discovery step changes the source of the ontology: it starts from spans that
endpoint428 finds expensive and asks an offline language model to propose
compression-native distinctions for those spans.

The language model is a research assistant only. It is not a teacher score,
decoder dependency, source allowance, or forecast input. Any proposed question
must be compiled into a deterministic rule over decoder-visible state before it
can enter an exact experiment.

## Local runtime receipt

The installed Gamma Python environment has no usable `torch` runtime for these
weights. No dependency or model was installed.

The local Vulkan llama.cpp completion binary is:

```text
path:    /home/x/src/llama.cpp/build-vulkan/bin/llama-completion
bytes:   4,850,248
sha256:  69af33f0b79e94b7c652238e83d941f510eb641bb1dcffd86216cc72f0269e4e
build:   b8017-f48842938
device:  Radeon 8060S Graphics (RADV STRIX_HALO)
```

The locally provisioned Gemma-4 GGUF is:

```text
path:    /home/x/models/gguf/gemma-4-e2b-it-q4-0-google/gemma-4-E2B_q4_0-it.gguf
bytes:   3,349,514,112
sha256:  3646b4c147cd235a44d91df1546d3b7d8e29b547dbe4e1f80856419aa455e6fd
```

That model is unavailable to the current llama.cpp binary because loading
terminates at `unknown model architecture: 'gemma4'`. This is a llama.cpp
runtime incompatibility, not a compression result. Do not convert, redownload,
or patch llama.cpp as part of the discovery lane.

The existing `/home/x/deco/gamma/.venv_rocm` environment provides a separate
candidate runtime: Python 3.14.4, Torch 2.12.1+rocm7.2, Transformers 5.13.1,
and native `Gemma4UnifiedForConditionalGeneration` support. With
`HSA_OVERRIDE_GFX_VERSION=11.0.0`, a synchronized 64x64 float32 CUDA matmul on
the Radeon 8060S produced SHA-256
`9ab0c29d311879d656d7fb6bd5ab0097c830911629ed27cccfef5265ea0ec5b1`.
This proves real ROCm compute. The full 23.9 GB checkpoint subsequently loaded
all 677 tensors, consumed at most 24,695,448,064 allocated GPU bytes, and
generated successfully from the frozen 1,081-token discovery prompt. The
greedy answer was exactly `REJECT`; output token IDs hash to
`c1d7d78b06cbcbd5222d7bde69be024b1566ccbedd955183587bf60d99664b68`.
The 12B ROCm path is therefore usable, but its answer remains zero-credit
discovery evidence.

The usable fallback is:

```text
path:    /home/x/models/gguf/qwen-3-5-2b-unsloth/Qwen3.5-2B-Q4_K_M.gguf
bytes:   1,280,835,840
sha256:  aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223
model:   Qwen3.5-2B, Q4_K_M
```

An initial `llama-cli` probe entered interactive conversation mode and was
terminated. It produced no corpus experiment and no scientific evidence. The
corrected one-shot `llama-completion` invocation used Vulkan, temperature zero,
seed 1, `--no-conversation`, and `--single-turn`; it exited zero and returned
exactly `LOGOS_RUNTIME_OK`. Reported prompt and generation rates were 55.40 and
106.13 tokens/s respectively. This proves only that the offline discovery path
executes on the installed GPU.

## Frozen discovery boundary

Only the development split, the first 60% of the 171 complete opening-1M
pages, may be inspected while creating the question vocabulary. Selection and
sealed-confirmation pages remain hidden.

For every eligible development clause:

1. Map its exact raw span to the WRT emission groups.
2. Sum endpoint428 bit loss from the receipt-bound exact P1 trace.
3. Rank by total parent loss and retain a diversity-controlled sample rather
   than repeatedly selecting one long page or one markup family.
4. Ask the offline model for binary questions that factor variable slots from
   reusable generated surface.
5. Reject any question requiring future bytes, latent embeddings, model
   inference, untransmitted knowledge, or a semantic judgment that cannot be
   compiled into deterministic decoder logic.

The initial read-only extraction found 2,957 eligible development clauses.
The highest-loss rows are dominated by long, unique prose, quotation,
citation, list, and link-rich constructions. High raw loss alone is therefore
not a bypass certificate; cross-page reusable fixed surface and exact MDL
economics remain mandatory.

The first frozen prompt presented twelve high-loss development examples to the
Qwen fallback. It returned `REJECT`, correctly observing that the sample was
dominated by page-specific facts and did not support byte-exact cross-page
generation. That answer does not become a candidate and does not authorize a
prompt or sample sweep. It narrows the useful successor toward a materially
different, deterministically mined information source rather than semantic
labels over long unique clauses.

The stronger local Gemma-4 12B checkpoint independently returned exactly
`REJECT` to the same hash-bound prompt. Agreement between the two models is not
a compression proof, but it is sufficient to stop this sampled discovery
attempt under the predeclared no-prompt-sweep rule. No variable-depth question
DAG was materialized and no selection or sealed page was opened.

Prompt and normalized answer:

- `docs/mobius2_residual_directed_discovery_prompt_v1.txt`
- `docs/mobius2_residual_directed_discovery_response_v1.txt`
- `docs/mobius2_residual_directed_discovery_gemma_response_v1.txt`

## Required successor gate

Discovery may materialize an adaptive proposal only after it yields one frozen
deterministic question language, an exact span boundary contract, literal
fallback, and shuffled/alignment controls. Its first experiment must be a
zero-cost exact ceiling on the opening 1M trace:

```text
parent payload identity                 exact
actual residual arithmetic payload      required
WRT and official raw reconstruction      exact
second payload                           byte-identical
development gain                         positive
selection gain                           positive
sealed gain                              positive
gross S2 gain                            >= 3,000 B/M
S2 total                                 < matched surface control
S2 total                                 < shuffled-question control
```

A miss retires the compiled question language without question-count, depth,
sample, prompt, or model rescue sweeps. A pass authorizes one paid grammar
format only. Forecast credit remains zero until counted native integration.
