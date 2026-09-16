# Lexical gate observation correction

`fx2_explicit_lexical250k_v2` preserves the exact codec sources, dictionary,
population, controls, compile commands and resource ceilings of
[v1](fx2_explicit_lexical_20260916.md). V1 was cancelled before any native phase:
the parent CLI refuses `--save-transformer-probs` with explicit `-d` decoding.
This is a pre-execution infrastructure correction, not a compression result.

The successor removes that unsupported request and its impossible equality
check. Every arm still independently decodes exactly to the bound raw input,
re-encodes the restored input, and repeats all exported encoding probabilities.
All arms' neural streams must match P. Decoder neural streams and full FXCM
state serialization are explicitly absent. The decoder's lexical activation
and lookup counts must still match its encoder and repeats. No scientific
parameter or decision threshold changes. The same 32 native phases apply.

The exhaustive dictionary tests and translation-unit checks bind the unchanged
codec materializer. The new runner passes source parsing; its observation
option is restricted to encode and repeat. This receipt grants no native gain
and no prize credit.
