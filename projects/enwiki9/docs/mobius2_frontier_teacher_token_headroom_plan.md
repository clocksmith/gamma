# MÖBIUS-2 frontier-teacher lexical headroom QH0

Candidate: `mobius2_frontier_teacher_token_headroom_qh0_v1`

Status: zero-credit teacher oracle. This is not a codec, source-bound score,
teacher package, or permission to ship a language model.

## Question

Does a locally provisioned causal language model assign enough proper
probability mass to exact raw realizations of WRT lexical events to expose at
least `3,000 B/M` of information that remains absent from the exact
JANUS-plus-quotient trajectory?

The experiment changes the information source. It does not add another WRT
suffix table, sparse residual DAG, recurrent-width variant, prompted clause
ontology, or copied-page prototype.

## Frozen population and alignment

Use complete pages wholly contained in the opening `1,000,000` raw bytes of
the canonical `10M` raw input. Split complete pages chronologically into first
60 percent development, next 20 percent selection, and final 20 percent sealed
confirmation.

Parse the exact WRT store into emission groups. A group contains any zero-raw
control events followed by the first output-producing event. The fast Gemma
tokenizer can represent one non-ASCII character as several byte-fallback token
IDs that all carry the same character offset. Normalize each maximal run of
overlapping tokenizer offsets into one tokenizer event and charge the sum of
the proper token NLLs in that event. This is an exact partitioning repair, not
an event selector. A Gemma tokenizer event is eligible only when:

1. its tokenizer offsets roundtrip to the exact raw byte span;
2. that span is an exact union of complete WRT emission groups;
3. at least one covered WRT event is a dictionary-token event; and
4. the span lies wholly inside one complete page.

No partial WRT event, tokenizer-crossing byte, or future raw byte is admitted.
The exact joint qbit charge for an eligible token is the sum over the covered
JANUS-plus-quotient P1 rows.

## Frozen teacher

```text
model:        /home/x/models/hf/google/gemma-4-12B-it
class:        Gemma4UnifiedForConditionalGeneration
tokenizer:    local fast Gemma tokenizer
dtype:        bfloat16 model execution, float32 log-sum-exp
device:       ROCm cuda:0
runtime:      HSA_OVERRIDE_GFX_VERSION=11.0.0
dropout:      disabled by eval and inference modes
context:      independent 512-token page-local blocks, each prefixed by BOS
```

The fixed block reset is part of the probability model. It avoids hidden
cross-page state and makes every probability decoder-causal. The language
model, tokenizer, logits, weights, and runtime are supplied free only for this
headroom question.

## Controls

```text
J0  exact JANUS-plus-quotient qbits on eligible WRT groups
U0  add-one Gemma-token unigram fitted on development pages only
G0  frozen causal Gemma distribution with the block reset above
```

U0 uses the complete Gemma vocabulary and remains frozen on selection and
sealed pages. It distinguishes contextual language information from a mere
change of lexical alphabet. Unknown or ineligible spans remain on J0 and do
not contribute gain.

## Measurement

For each split `s`:

```text
gain_G(s) = sum eligible [joint_qbits / 256 - gemma_nll_bits]
gain_U(s) = sum eligible [joint_qbits / 256 - unigram_nll_bits]
B/M       = gain_bytes * 1,000,000 / represented_raw_bytes
```

This is ideal proper-distribution codelength, not an arithmetic archive. No
per-token oracle selector is permitted. Every eligible token is charged to the
named teacher or control, including regressions.

## Integrity gates

Require:

```text
all input and model hashes recorded
ROCm matrix compute in the declared runtime succeeds
model logits finite and probabilities normalized by exact float32 logsumexp
tokenizer page roundtrip exact
WRT parse reconstructs the canonical raw bytes exactly
joint P1 row count and truth alignment exact
eligible spans nonoverlapping and emission-group exact
repeat calibration NLL hash byte-identical
```

A nonzero process status means malformed inputs, failed causality/alignment,
invalid logits, nondeterminism, or runtime failure. A scientific `PASS` or
`REJECT` exits zero.

Score development first. If complete development gain is nonpositive, emit a
valid `REJECT` with selection and sealed confirmation marked `not_opened`.
This deterministic early kill follows directly from the promotion rule and
prevents a negative teacher from consuming or informing later splits.

## Decision rule

Authorize one residual-directed compilation study only when:

```text
development G0 gain                  positive
selection G0 gain                    positive
sealed G0 gross gain                 >= 3,000 B/M
sealed G0 codelength                 < sealed U0 codelength
eligible sealed raw coverage         explicitly reported
all integrity gates                  pass
```

A pass grants no score credit and does not authorize model distillation,
native integration, or a larger corpus run. It only permits attribution of
the paying tokens and one compiled deterministic rule-language proposal.

A miss retires this exact Gemma-4 12B checkpoint, tokenizer-event alignment,
512-token reset contract, and unigram control without model-size, prompt,
context-width, tokenizer, or threshold sweeps. The next lane must use a
different external knowledge source or a constructive corpus generator.
