# Explicit lexical input to the native predictor

Candidate: `fx2_explicit_lexical250k_v1`. This is an activation of existing
upstream FXCM word and stemming models, not a claim of novel lexical modeling.
The unchanged trimmed parent remains the comparator.

The closed attention gate saved zero bytes and is retired. The earlier ambient
dictionary diagnostic decoded an archive produced without `.dict`; enabling
that file only during decoding failed after pretraining. That establishes an
undeclared input mismatch, not the performance of matched lexical predictions.
In the tested parent, `isDictLoaded` remains false and `codeword2sym` remains
zero. Existing complete-word spellings and partial dictionary-index contexts
therefore remain disabled. The explicit frontend dictionary is already paid.

Discovery uses deliberate lenses 2 and 9: recover known surface spellings from
token IDs, then test their contribution to the existing context specialist.
Designer, decoder, and skeptical-review passes selected this concrete missing
input over two alternatives: another grammar/template representation (deferred
after its negative matched results) and another exact weight-storage change
(deferred because it cannot alone provide the required payload improvement).
No attention-retention, window, final-output residual, or grammar rescue sweep
is authorized. This is one native comparison on exposed opening 250KB.

Both encode and decode explicitly load the bound 44,515-line dictionary after
unchanged ordinary pretraining and before coding. File position is restored.
The loader accepts only bounded lowercase newline-terminated words. There is
no working-directory lookup. The existing codeword-index formula is retained;
synthetic tests check every 44,880 representable index against the independent
frontend formula. An out-of-range completed index emits an empty lexical
prediction and resets the word index to zero; its count is reported. It does
not change decoded bytes. The inherited stream parser is a predictive feature
extractor, not the authoritative frontend inverse.

Arms:

- P: unchanged trimmed native parent, with no ambient `.dict`.
- K: load and validate dictionary but leave all predictive globals disabled.
- D: enable the existing partial-index and complete-spelling model.
- S: same index mapping, but cyclically shift dictionary spellings by one.

S disrupts index-to-spelling association rather than relabeling an invertible
learned feature space. Its word-length and morphology effects are part of the
control; a pass would support this matched association, not semantic causality
in general. D and S intentionally change FXCM and downstream mixer states.
The transformer, PPMd, frontend, weights, update rules, and arithmetic coder
remain unchanged. All exported neural probability bytes must match P across
arms and encode/decode/repeat. P/K archives must be byte-identical. Full FXCM
state serialization is not provided. Runtime mode and lookup counts must agree
across each arm's encode, decode, repeated encode, and untraced encode.

All arms have two clean builds, exact raw inverse, deterministic raw re-encode,
and trace-off archive identity. Source ZIP and executable prices are separate
component alternatives. The mode is a literal source constant, not an extra
runtime or build option. Every required dictionary/model is retained; none is
free in final packaging. Unknown complete package and full1G score stay unknown.

The 32-phase gate uses CPU2, memory 9,999,998,976 bytes, swap zero, logical
scratch 16,000,000,000 bytes, and aggregate stop 3,600 seconds. Timings are
shared-host diagnostics. The exact original 33,429-byte parent archive must
be reproduced. Hypothesis passes only if D beats P and S, and its gain pays
the measured incremental source ZIP. A positive unpaid gain is held; a valid
nonpositive parent/control margin retires this realization. Missing evidence,
correctness errors, or resource stops are incomplete, not compression losses.
Only a pass authorizes unchanged independent confirmation. No larger scope,
full-corpus projection, or prize claim follows from this development sample.
