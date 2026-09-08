# forge-cmix — algorithmic description (Hutter Prize rule: idea documentation)

## Pipeline (inherited from the fx2-cmix lineage)

1. **Article split & reorder**: enwik9 is split (intro/main/coda), articles are
   permuted by a precomputed similarity order (`new_article_order`, embedded in
   the executable) so related articles become adjacent.
2. **Dictionary/WRT transform**: frequent words are replaced by short codewords
   (`english.dic`, embedded), plus the phda9-derived preprocessing.
3. **Context-mixing compression**: the transformed stream is compressed by a
   PAQ-family context-mixing coder: several hundred context models feed a
   mixer network; an LSTM acts as a byte-level mixer/predictor.
4. **Self-extraction**: `archive9` = decompressor stub + embedded dictionary,
   article order and compressed stream; running it reverses steps 3→1 exactly.

## This project's contributions (details in MODIFICATION-RECORD.md)

- **fxcm_v26 integration**: Kaido Orav's strongest published text-model family
  (as integrated by cmix-lex) is ported into this tree's predictor stack.
- **compact23 output reduction**: instead of exposing every fxcm_v26 predictor
  output to the mixer, a masked subset (group mask 23; 403 configured outputs,
  one compact output stream) is used. Rationale: most of the added outputs are
  redundant with existing models; pruning them cuts mixer work and memory
  while keeping the informative signals — this is what makes the strong model
  affordable inside the 10 GB / normalized-time box.
- **auxmatch**: one auxiliary match-model output (aux mask 1) is kept from the
  v26 family to strengthen long-range repetition prediction.
- **elision**: redundant per-byte model updates are skipped where provably
  inconsequential, reducing time; bound by a preregistered provenance chain.
- **cells270**: the LSTM byte-mixer is resized from 300 to 270 cells: with the
  v26 models present, the LSTM contributes less unique signal per unit time,
  and 270 cells rebalances the time budget in favour of the model ensemble.
- **anon-THP advisory**: the process advises the kernel to back its large
  anonymous allocations (hash tables, LSTM weights) with transparent huge
  pages, reducing TLB pressure; correctness does not depend on THP being
  available (audited via stderr status markers).

## Why it compresses better

The gain over fx2-cmix comes from (a) the stronger v26 text models made
tractable by output pruning, and (b) reinvesting the saved time/memory into
the ensemble rather than raw model size. The result is verified lossless:
`./archive9` restores enwik9 bit-exactly (sha256
`159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`).
