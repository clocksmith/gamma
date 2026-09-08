# Research Register Archive - part 046

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-09-06 - Competing Gemini design and blind decoder review

ROOT owns one bounded [Gemini design request](../../../operations/provenance/dualstream_gemini_design_20260906/request.md)
using the installed CLI and existing authentication. Its request manifest binds
the measured v1 source, synthetic tests, exact opening development input and
terminal failure. It asks for one implementable successor, encoder/decoder
procedures, termination and inversion arguments, complexity and a falsifying
test. Model output is a proposal with zero evidence or score authority.
Tools, extensions, MCP and hooks are disabled; validation/confirmation bytes and
model-campaign artifacts are withheld. A separate reviewer starts from codec
source and synthetic fixtures without result claims. Publication precedes the
request; a returned design still needs implementation, independent inverse
review and a separately frozen exact comparison before it can advance.

The request was published at `2eff25f26ba4bc3022f68b1ea9853843b740aae6`.
The installed client then failed authentication with `IneligibleTierError`:
its Code Assist access was reported unsupported. The retained execution receipt
has return code 1 and an empty response. No Gemini proposal or model-quality
claim follows; no dependency installation or credential change was made.

The independent reviewer found a separate v1 inversion failure for one-byte
frames: 74,074 identical bytes produce an archive above the decoder's cap.
ROOT's new `dualstream_grammar_bounded_v1.py` checks each write against the same
cap and preserves accepted v1 archive bytes and source. Eighteen synthetic tests
pass, including the reported boundary and atomic file rejection. This repair
is locally authored; it is not a Gemini design or new corpus compression result.

The user explicitly removed Gemini from the required workflow. This consultation
attempt is closed; authentication or another provider is not a research blocker.
Continue locally from the measured literal-definition cost, with independent
review and exact benchmark comparisons. Keep the failed request as historical
provenance and keep confirmation inputs withheld from development.
