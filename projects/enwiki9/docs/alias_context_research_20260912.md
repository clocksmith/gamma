# Alias-conditioned prediction research, 2026-09-12

The selected hypothesis is **decoder-learned alias equivalence for predictive
context sharing**. It is a bounded research candidate, not an established best
compressor or a global novelty claim. The first comparison is deliberately
synthetic. Its role is to falsify the causal mechanism before spending a corpus
budget. Owner: `root_alias_research`; candidate: `alias_context_fixture_q0_v1`.

The user suggested quines, acronyms/abbreviations, sparse attention and
self-referential prompt exploration. Creative-discovery lenses 2 and 9 were
selected deliberately: distinguish an entity from its exact spelling, then test
whether its specialist contributes information beyond a matched baseline.

## Three hypotheses and decisions

| Hypothesis | Information exploited and costs | Discriminator and decision |
|---|---|---|
| Self-executing recursive description, including a quine or paid prompt | Repeated structure expressed by a program; all source, seeds, prompt selection, exceptions and termination information count. | Reject the claim that self-reference itself removes payload information. Recursive grammar compression remains legitimate, but needs a concrete new grammar family and measured accounting. No quine wrapper is added. |
| Alias-conditioned sparse prediction | Completed text explicitly relates a long name to an abbreviation. Share subsequent predictive statistics across those spellings while coding every surface byte exactly. Parser, counts, fallback and any transmitted choices count. | Selected. Compare literal labels P, discarded bookkeeping K, relation sharing D and wrong-association S. Keep the model bounded and cold. |
| Neural sparse attention or a generic retrieved continuation | Select a small part of history to reduce memory/compute and preserve useful predictions. Model weights, routing, training, index and coder costs remain. | Plausible resource technique, but existing local retrieval failures rule out endorsing unchanged generic retrieval. No new network or model download is justified by this review. |

## Why quines do not supply free information

For one fixed deterministic terminating decoder and N-bit inputs, there are
only `2^N - 1` bitstrings shorter than N bits, including the empty string.
Consequently an injective lossless description cannot shorten every N-bit input.
Self-reference does not change this counting argument. It does not rule out a
short program for one particular structured corpus; that program and its inputs
must still be supplied and counted. Cyclic expansion must terminate with one
unique byte string. A hash of missing bytes does not supply their preimage.

For a prompt-selected predictive model, the actual objective is the finite
archive length plus the prompt, model, decoder and other charged package bytes.
An encoder-selected prompt using unseen page text must be transmitted before
its predictions are used. A prompt deterministically reconstructed from the
decoded prefix needs no separate label, but only accesses information already
available to the decoder. Bayesian marginalization can replace an explicit
selector: in exact arithmetic, a prior mixture satisfies
`-log2 Q(x) <= -log2 P_j(x) - log2 pi_j` for each included model j.
That is a bound relative to those models, not a promised compression gain;
finite probability quantization, coding termination and software cost still count.

## What the literature establishes

- [Yeates, Bainbridge and Witten (2000)](https://arxiv.org/abs/cs/0007003)
  already use compression to identify acronyms. Their method encodes letters
  relative to definition words, including preceding and following windows.
  This establishes prior art for acronym modeling. Using future definitions
  would require explicit coding order or side information in a causal codec.
- [Russo et al. (2020)](https://arxiv.org/abs/2003.02336) study bidirectional
  macro schemes and report advantages over Lempel-Ziv on artificial repetitive
  texts. Those results do not establish superiority over a strong enwik9 model.
- [Infini-gram](https://arxiv.org/abs/2401.17377) shows that extended n-gram
  prediction can complement neural models. A large external index is not free
  decoder history; the candidate here reconstructs its small dictionary online.
- [Native Sparse Attention](https://arxiv.org/abs/2502.11089) targets efficient
  long-context modeling. Prediction quality and compute benefits are distinct
  from a fully counted lossless archive under this project's resource rules.
- [Language Modeling Is Compression](https://arxiv.org/abs/2309.10668)
  motivates evaluating predictive distributions as code lengths. Its results
  do not supply a small self-contained decoder for this candidate.

These are primary sources. Their implementations and weights are not imported;
there is no new external code license or model dependency in the prototype.
The literature search is not exhaustive and cannot certify global novelty.

## Local evidence that changes the design

The [SRSTC residual-program rejection](../operations/adaptive/exclusions/srstc_residual_program_candidate_universe_nonpaying_v1.json)
and [JANUS suffix-DAG rejection](../operations/adaptive/exclusions/janus_sparse_context_dag_opening1m_v1.json)
show why generic self-referential memory or a renamed suffix table is insufficient.
The [SIBYL page-prompt result](../operations/adaptive/exclusions/sibyl_page_calibration_opening1m_v1.json)
saved 7 gross bytes and lost 33 after labels on its opening-1M replay.
That rejects the tested calibration selector, not every possible prompt model.
Historical cards calling SRSTC the primary novel strategy are not current
positive transfer evidence; canonical terminal results take precedence.

The new information coordinate is an **explicit equivalence edge**, not a
nearest-neighbor match or the previous word alone. It transfers evidence about
what follows an entity, rather than replacing the acronym with a copy pointer.

## Exact first discriminator

The [prospective contract](../operations/adaptive/experiments/alias_context_fixture_q0_v1.json)
and [fixture specification](../operations/planning/alias_context_fixture_q0_v1.json)
bind four synthetic inputs totaling 10,888 bytes. A completed line such as
`Aster Beacon (AB)` installs an alias; a later `AB:` payload can use observations
from `Aster Beacon:`. This explicit line grammar is a test interface, not a
Wikipedia parser. Abbreviation recognition is deliberately restricted.

All arms use one Q16 arithmetic coder, an order-8 bit-count fallback, at most
4,096 conditional-count rows with FIFO eviction, and one fixed mixture. D and S
read at most 16 learned alias entries; this is sparse associative lookup, not a
trained transformer attention layer. No large model, embedding or prompt is sent.

P uses literal entity spellings. K records and discards the alias dictionary.
D maps abbreviations to their learned full names. S maps each abbreviation to
the next full name in dictionary order, preserving literal full-name contexts.
A bijective renaming of every identifier would preserve equality relations and
would be an invalid sham control; S changes the edges instead.

Each arm independently encodes, decodes and repeats each input. Retain every
archive, exact inverse, full terminal state and hash witnesses for probabilities
and all predictive state at every byte. Compare P/K byte identity and predictive
state while excluding K's deliberately discarded dictionary. No-definition and
binary controls must produce the same archives in all arms. The wrong-relation
fixture tests harmful sharing; its result is reported, not used to tune weights.

Admission bounds: CPU2, 536870912 memory bytes, zero swap, 67108864 scratch bytes
and 120 wall seconds. A resource stop is an incomplete comparison, never a
compression regression. A positive fixture result proves only constructed
transfer under this parser and weak baseline. Natural-text frequency, overlap
with the strongest predictor, source amortization and full package costs remain
unknown. No fixture gain may be extrapolated into a corpus forecast.

The next scientific discriminator, if feasibility passes, is a separately frozen
natural-text opportunity/cost study against the actual stronger parent, with
matching frontend coordinates, article-local definition scope, ambiguity and
alias-redefinition tests. It must show residual value after source cost before
any larger comparison. The previous cold 1MB word experiment remains separate.
