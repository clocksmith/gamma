# Causal closing-name replay

Owner `root_explore`; separately identified component `fx2_closing_replay_v1`.
The [synthetic plan](../operations/provenance/fx2_closing_replay_v1_synthetic_plan.json)
selects discovery lenses 5 and 6 after the native XML context coordinate failed
to save archive bytes. This component predicts stored bytes from a previously
decoded opening name; it does not change that failed context key.

The historical WIKI-PDA scanner's truth-before-credit defect is recorded in
[part 024](research_register/archive/part-024.md). Its superseded q1 contracts,
transition tables, full-population thresholds and ownership remain unchanged.
This component uses only closing-name replay on the FX2 stored alphabet,
64-byte names and depth 16. It inherits no scientific result or qualification.

The current FX2 `Bracket::ByteUpdate` tracks delimiter pairs and distances.
The hypothesis here is that stored opening-name spellings retain additional
useful information. No useful corpus opportunity frequency is yet established.

The [implementation](../lib/fx2_closing_replay_v1.hpp) keeps bounded stack,
name, attribute-quote, escape and closing-position state. Both sides can call
`predict()` before supplying the next stored byte to `observe()`. Only a
decoded closing slash enables a donor. A mismatching name byte disables
remaining replay; a mismatched completed closing name clears the stack.
Self-closing tags do not push. Escapes, unsupported markup and overflow
conservatively clear uncertain state. This is a stored-spelling recognizer,
not an XML validator or an assertion that all its donors are correct.
In particular, the first mismatching byte must still be scored against its
pre-observation donor; abstention takes effect only on later bytes.

WRT byte swapping is undone only for recognizing syntax. Names are retained
and predicted in their exact original stored coordinates, including dictionary
code bytes. No dictionary lookup or future truth is supplied to `predict()`.
The component does not validate WRT codewords; a later gate must independently
bind the valid frontend and population. It does not reconstruct raw XML.

Every future-affecting mutable field is included in the 1,124-byte state
serialization. The state method is an audit representation, not a checkpoint
restore API. The [unit receipt](../results/fx2_closing_replay_v1_unit/attempt01/receipt.json)
retains source preimages, optimized/UBSan executables, logs and seven passing
tests. Each fixture repeats in both builds. Tests cover prediction timing,
nested names, quoted attributes, self-closing tags, first mismatch, overflow,
uncertain markup and stored multibyte names. This is synthetic correctness only.

Next freeze one separate opening250KB opportunity-cost gate using the retained
unchanged native parent trace. Score before observing each current truth,
bind byte/bit coordinates and exact parent probabilities, and record active,
correct and incorrect donors, chronological partitions and shifted controls.
An optimistic cost ceiling must explicitly keep the opportunity set and parent
fixed; it is neither a finite-archive bound nor a full-corpus impossibility
result. A useful ceiling authorizes a measured causal codec comparison only,
with package costs, matched controls, independent inverses and deterministic
repeats. No corpus gate or native integration has been launched for this component.

Independent read-only review found no blocking causal or bounds defect and
confirmed complete state serialization. It emphasized that WRT case state and
token widths are not validated here: apparent stored syntax need not be a true
raw XML closing tag. Corpus donors must be scored as fallible predictions.
The review's four additional [boundary groups](../results/fx2_closing_replay_v1_unit/boundaries01/receipt.json)
also pass optimized/UBSan builds and repeats: exactly64-byte names, depth16,
case controls/escaped markup and equal current predictions whose future differs
because of earlier stack contents. The measured component source is unchanged.
