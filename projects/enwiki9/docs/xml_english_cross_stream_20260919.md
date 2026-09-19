# XML, English and information shared between streams

The [bounded census and first causal-history comparison](xml_history_census_20260919.md)
is complete: the exposed opening250k has 14.96% outer XML/metadata and 85.04%
article-body bytes. Joint Deflate history beats shifted donors by473 bytes but
loses61,311 bytes to unsplit coding. Its fixed framing/dictionary realization is
retired; the measured metadata-to-text opportunities remain a research input.

The active [v4 objective](../contracts/research/v4/objective-contract.json) is
at most **96,000,000 fully counted bytes**, with **95,000,000** as the stretch
target. Smaller packages also pass. This deliberately replaces the 90M planning
target while preserving every earlier contract and measured result.

The research direction is the user's XML/English decomposition: improve each
stream and exploit references between streams. The approximate 25%/75% split is
a working hypothesis about raw bytes, not a measured allocation of compressed
cost. Outer XML, metadata values, article prose, Wiki markup, entities, URLs,
numbers and exceptional bytes must be distinguished in the census. Article
content is not uniformly English prose. Every byte needs an exact owner and
original coordinate; residual categories must not disappear into a percentage.

## What the zmix study establishes

[Mahoney's published entry](https://mattmahoney.net/dc/text.html#0960) identifies
James Byrne's September 14 submission as still under committee testing. Its
reported self-extracting archive is 96,096,261 bytes; the compressor adds
3,216,163, giving 99,312,424 before independently checking required options.
The republished author writeup describes a Zig implementation of the established
cmix model stack, retrained transformer weights with a weight-size objective,
more compact model storage, a smaller decompressor, and changes to statistical
models and mixing. Its dictionary is derived during compression.

This establishes a concrete public submission and plausible mechanisms, not
verified prize eligibility or independently reproduced gains. The author's host
returned HTTP 403 for direct documentation access here; no source audit or
execution of zmix is claimed. Relevant lessons are to optimize archive and
package jointly, measure complementary predictors, and price shared assets.
The published description does not establish our proposed two-stream design.

The [dated competitive snapshot](../operations/provenance/competitive_frontier_20260919.json)
separates the displayed official record, zmix, and an indexed committee-member
report of another pending 98,249,835-byte entry. If the latter exact total becomes
the accepted reference, the next 1% threshold is 97,267,336 bytes. The 96M ceiling
leaves 1,267,336 bytes below that conditional threshold; 95M leaves 2,267,336.
Neither is a guarantee against intervening submissions or accounting changes.

## Existing evidence and the changed premise

The retained [event comparison](../operations/provenance/dualstream_event_terminal_20260907.json)
on the exposed opening 250KB reports plain Deflate 89,041 bytes, grammar Deflate
102,492, sequential grammar events 116,986, and interpreter-conditioned events
117,345. Interpreter context added 359 bytes. The
[literal-first comparison](../operations/provenance/dualstream_literal_first_terminal_20260907.json)
fell back exactly to the 89,041-byte parent after its evaluated templates failed
to pay. These scoped losses remain valid and do not reject all structured or
cross-stream models.

The [shared-argument fixture](../tests/test_dualstream_selection_diagnostic_v1.py)
demonstrates exact reuse of repeated field values on invented data. Its positive
control is implementation evidence, not an enwik9 forecast. Existing WRT
[TWINSTREAM code](../tools/wrt_twinstream_shadow.py) already enforces visibility
only after a complete emission group; reuse that causality rule. Its NNCP/WRT
stream terminology must not be confused with the proposed XML/English split.

The changed premise is **conditional prediction from a shared, decoder-visible
reference history**, initially preserving the representation and coder. Do not
repeat a losing grammar serialization under a different candidate name.
The retained [opcode/previous-word confirmation](opcode_previous_word_confirmation_1m_20260912.md)
also provides a closer native parent: its register reports 737 archive bytes
over P and 313 over its semantic control on the exposed 1MB comparison.
Verify that exact closure and state interface before selecting it; the weaker
Deflate experiments alone do not establish the strongest compatible parent.

## Concrete stream design

1. **Exact events and routing.** Scan bytes without XML normalization. Assign
   syntax, metadata values and text spans to typed events; preserve whitespace,
   entity spelling, malformed/truncated markup and arbitrary bytes literally.
   Emit any routing and length information before the decoder needs it. Keep
   raw-byte and transformed-symbol coordinates distinct.
2. **Within-stream models.** Use XML parser state, tag/attribute position and
   repeated metadata patterns for structure. Use lexical, phrase and context
   predictors for content, with Wiki markup and numeric/URL contexts explicit.
   Compare the split against the same unsplit parent and count routing costs.
3. **XML to text.** Already decoded title and field type can predict body words;
   decoded link targets and citation fields can supply exact or delta-coded
   spellings. Reuse the available title/reference parsers before adding another.
4. **Text to XML.** Completed words, links and prior citations can inform later
   metadata values or repeated field contents. Outer tag syntax may already be
   cheap; require measured residual cost before allocating model capacity.
5. **Shared referential memory.** Start with page-local bounded entries indexed
   by exact decoded spelling and field role. A reference either names a prior
   entry or pays to introduce one. Delta edits, reference IDs, escapes, resets,
   eviction, model tables and reconstruction code all count.

Physical streams may have separate arithmetic states, but decoding follows one
declared event schedule. A donor becomes visible only after its producing event
has decoded. No stream may require the other's undecoded future. If a two-pass
variant transmits a title dictionary first, charge its bytes and initialization
explicitly. That is a separate candidate from causal first-use memory.

## First comparison and decisions

First establish a census of raw shares and parent coding costs by event type,
using existing exposed bounded data and original-coordinate ownership. Track
metadata values separately from syntax. Freeze one parser, one memory bound,
one event schedule and one parent before predictive comparisons.

| Arm | Purpose |
| --- | --- |
| P | Unchanged unsplit parent |
| B | Same parent with stream routing and within-stream models only |
| K | B with shared-history bookkeeping; predictions unchanged |
| X | K plus XML-to-text information |
| E | K plus text-to-XML information |
| J | Both directions together |
| S | J with unrelated but already decoded donors; same opportunities and capacity |

K must reproduce B's archive and declared predictor/coder state. Compare X/E
with K to identify direction-specific benefit and J with both single-direction
arms to measure overlap. J must beat P after complete package/routing costs;
beating the shuffled control alone is insufficient. Do not sum X and E gains.
Losses stay attributed by event category rather than being hidden by a global
average. A wrong-donor control may never see future text.

Acceptance requires independent decode, raw-encoder repeats, equal encoder/
decoder reference state, exact source/asset closure, real finite archive bytes,
and bounded resources. Use the existing synthetic binding test as a positive
control; add no-benefit, missing-donor, malformed-input, eviction, entity-spelling
and attempted-forward-reference fixtures for the selected implementation.
Choose one mechanism after the census. Freeze its smallest experiment through
the lab before execution, then use a separately frozen disjoint confirmation
population. Existing exposed opening data cannot be relabeled as held out.

This document records source study and research selection, not a compression
result, new queue, corpus launch, or permission to promote historical candidates.
The next executable research step is the exact byte/coding-cost census and
donor-availability test; full-corpus score and composition gains remain unknown.
