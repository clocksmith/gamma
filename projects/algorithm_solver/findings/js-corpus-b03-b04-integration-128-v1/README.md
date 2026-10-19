# B03/B04 bilingual corpus integration

The versioned [catalog](catalog.json) contains **58 unique problems** with58 JavaScript
and58 Python implementations. It preserves the24-problem predecessor and adds the
requested33 B03/B04 candidates plus115 after its exact-integer contract review.
There are5,095 matched independent cases per language; this is10,190 language
executions, not10,190 unique test cases. IDs and language-agnostic keys are deduplicated.

[Integration evidence](integration.json) binds sources, provenance, normalization,
test and receipt hashes. The private bodies are in
`data/derived/bilingual_development_corpus_v2/{javascript,python}/`; the index is
`data/derived/bilingual_development_catalog_v2.json`. A JS-onlyv2 index is also
available. No production loader or Python recognition catalog changes.

## Seven conflicts reviewed

[Per-ID conclusions and source evidence](conflict-review.json) link the
[exact private report](../../runs/js-corpus-contract-review-128-v1/EXACT_REVIEW.md),
which includes failing inputs, expected values and both actual results.60,65,74,81
and87 have nine failing test rows outside their pinned input domains. Python's
incidental match on those cases does not establish an in-domain candidate bug or
a legitimate generalized oracle. All five remain excluded; no expected value was
rewritten and no failing case was silently removed.

78 and90 have a genuine shared-wave contract defect: exact outer-array ordering
contradicts the statements and even gives conflicting expectations for identical
inputs. The isolated [v2 correction](subset_order_v2.py) changes only the comparison
declaration for the exact uid/slug/method identities. It reuses the tested
multiset comparator, retaining inner order,types and multiplicity. One case per
sandbox invocation avoids aggregate output truncation without raising the64KiB
cap. [Eight independent control groups](test_subset_order_v2.py) pass. Unchanged
original algorithms in both languages pass91/91 and103/103 independent cases and
all four public cases. These two corrected results remain separate from the
explicitly requested33+115 integration; the integrated count is58, not60.

## Exact-integer115 review

[115 review](115-review.json) verifies all existing transport/runner hashes, the
101/101 independent results in both languages, two public cases and four input
preservation probes. Five additional combinatorial checks use independently
derived binomial coefficients, including60-choose30 and100-choose50. Native
BigInt results remain exact; unsafe Number output is rejected. This qualifies
the explicit BigInt-capable development implementation, not arbitrary runtimes.

The33 B03/B04 additions have2,777 independent cases. Their style-only ancestors
preserve all40 original qualification outcomes and95 public result/mutation/
reference-alias observations;62/69 are explicitly separate numeric successors.
The prior B04 console count1849 was a label typo: the actual frozen assignment
and receipts contain1749 cases. No test selection changed.

The next lane is broader paired-corpus coverage and semantic macro discovery.
Histogram stack84/85 and inorder94/98 are candidate shared patterns, not newly
qualified macros. There is no new predictor campaign, training, protected scoring,
public push, deployment, autonomous solve or language-codebook promotion here.
