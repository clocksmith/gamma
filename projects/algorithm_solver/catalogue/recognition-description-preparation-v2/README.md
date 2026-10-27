# Recognition description preparation v2

Private candidate preparation, not a generated index or a deployed release.
The aggregate machine-readable receipt is [STATUS.json](STATUS.json). No statement,
normalized description, identity membership list, vector, or private packet is
included in this source-only change.

## Measured preparation

The current pinned catalogue remains 4,081 identities: 2,872 authorized, 482
reserved, and 727 unresolved. The latter number is a fresh classification count,
not the historical description backlog. There are no duplicate identities or
known alias collisions; complete alias closure is not claimed.

425 exact, authorized statement artifacts add descriptions without overlapping
any of the previous 153 prepared descriptions (102 reviewed normative contracts
and 51 development-authored candidates). Ten further exact official statement
prefixes add disjoint, explicitly partial descriptions. The candidate contains
**588 prepared descriptions**, with **2,284 authorized descriptions still missing**
and 3,493 exact title-only competitors. All identities and their original order stay
present, independently of implementation availability. Reserved and unresolved
competitors retain their frozen title text and existing vectors.

The consistent rendering changes all 588 rich documents relative to the original
102-description vector baseline: **3,493 vectors are proven reuse-eligible,
588 require generation, and zero have been generated**. No identity is added or
removed. Reuse eligibility is not a claim that a complete new vector file exists.
Encoder, model, adapter, tokenizer, pooling, normalization, execution identity,
and 1,024-token truncation stay unchanged. Historical indexes are not equated by
dimension or assigned invented provenance.

## Schema and source discipline

[recognition_description_schema.py](../recognition_description_schema.py) defines
intent, input, output, constraints, effects, and distinguishing details. Each field
carries its state, exact artifact hash and clause selector. Unknown is not false,
unconstrained, or a fact inferred from implementation. IDs, availability and
qualification labels are not ranking text. Original IDs, titles and verified
aliases remain bound separately.

[recognition_statement_extraction.py](../recognition_statement_extraction.py)
revalidates the pinned policy immediately before each exact statement open and
checks the locator, hash, byte count, bounded read and no-symlink traversal. It
retains exact definition/constraint clauses, preserves mathematical superscripts,
and excludes explicit example sections/outputs, hints, solution sections and
preformatted blocks by default. Optional follow-up conditions stay optional.

Two explicitly recorded private manual projections repair an input-clause label
and recover a normative preformatted definition omitted by the conservative
extractor. The latter is part of the problem definition, not a proposed solution.
Original extraction files remain unchanged. Independent semantic review now covers
all 425 extractions and the ten selected-prefix descriptions. It approved 65
additional field corrections and held three optional removals because inline
illustrations may carry definition details. Eight definition-image rows were
checked: four are text-sufficient and four require normative diagrams. The four
exact referenced images were acquired through permission gates, verified by byte
and Git-blob hashes, visually transcribed and independently reviewed. Their
composite authorities retain the original statement/image hashes; no historical
image equivalence or general rule inferred from displayed values is claimed.

Of the 435 new descriptions, 434 have reviewed projections and one is explicitly
`independently-reviewed-incomplete`; its selected definition does not establish
representation order. Other source ambiguities remain documented, not repaired
from examples or implementations. Selected official prefixes are partial: missing
bounds/effects remain unknown, and no equivalence to historical HTML is claimed.
Mechanical checks or manual semantic review are **not** recognition or
implementation qualification. Prior 153 fields retain their prior evidence class.
587 effects fields remain unknown; one contains a source-backed partial effect.
Unknown means unclassified in this description, not absent from its source.

Raw authorized statements contain public example sections; those sections are
excluded. Inline illustrations inside normative definition paragraphs may remain. No separate source/case file or protected payload was opened.
Acquisition permission does not grant publication permission. Private documents,
per-ID backlog, manual overlays and exact acquisition receipts remain outside Git.
The backlog is a projection of the existing registry, not a competing registry.

## Bindings and verification

Candidate preparation identity:
`75d3482139bcd0ce763b042c1b66f2beafc022c342bdc70db37e3869f0de428b`.

The private manifest binds descriptions, normalized semantic metadata, order,
aliases, original baseline rows and unchanged execution. Matching existing BITS
metadata/packet-plan keys are verified for all 4,081 identities and bound to this
candidate. No solution guides, vocabulary changes or editor assets are included.
All original baseline rows were checked for exact vector hash/order, 1,024
dimensions, finite values and normalized norms; changed-document bindings passed
without constructing the encoder or starting a worker. Rendered rich documents
are 406–2,764 characters; this is not a token/truncation measurement.

Focused synthetic schema/acquisition tests plus existing candidate/search/bundle
regressions: **108 passed**, of which 42 exercise the new schema/extractor.
Private review checks also replayed 62 proposed field overlays and rejected 62
self-consistently rehashed invented-value controls; 24 composite-authority
tampering controls and 37 prefix-span controls were rejected. These are development
integrity checks, not retrieval metrics or held-out confirmation results.

```sh
PYTHONPATH=.:projects/algorithm_solver python -m unittest \
  projects.algorithm_solver.catalogue.test_recognition_description_schema \
  projects.algorithm_solver.catalogue.test_recognition_statement_extraction \
  projects.algorithm_solver.catalogue.test_recognition_inventory \
  projects.algorithm_solver.catalogue.test_recognition_search \
  projects.algorithm_solver.catalogue.test_recognition_candidate \
  projects.algorithm_solver.tests.test_recognition_bundle
```

## Open gates

- No embedding run: an established hard aggregate process-group memory cap is
  still missing. Do not weaken the existing resource envelope or rebuild all rows.
- The recorded available memory was 3,015,970,816 bytes, below the unchanged
  5 GiB floor. No encoder, tokenizer or worker was started. Capacity alone would
  not remedy the missing hard aggregate cap.
- Before any recognition claim, resolve or explicitly retain semantic exclusions,
  generate the eligible changed vectors, measure actual truncation, recalibrate the changed competitor
  population, and report recall, variants, ranking, ambiguity and cold/warm
  latency separately on permitted development data. Confirmation remains closed.
- No publication/activation: exact permitted public assets and an established
  existing deployment target remain unverified. Live lookup is not verified.
- Existing coherent activation/rollback code has synthetic regression coverage;
  no actual deployed snapshot or rollback has been created or exercised here.
  See the [earlier release-tooling receipt](../recognition-candidate-release-v1/README.md).

Component intent and qualification/permission boundaries are unchanged.
