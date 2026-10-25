# Versioned correction notice

This successor preserves v1 without edits. Independent review found that v1
incorrectly marked generic sorted input SATISFIED against the strict/distinct
rotated-array authority. V2 marks that relation UNKNOWN without an explicit
distinctness premise. V1 is not silently relabeled or retrospectively repaired.
The predecessor freeze, review receipt, all local files, and imported dependency
modules are pinned in `freeze.json`; run `verify_freeze.py` before integration.
No cohort has been evaluated for this correction.

# Description applicability v2

Prospective goal 1b **veto-only empirical guard**, not a qualified recognizer.
Intent preserved: one description, zero questions, all 4,081 competitors, and
exact separately qualified JavaScript/Python retrieval. No source execution,
encoder invocation, query cohort inspection, model downloads or training.

## Mechanism and authority

`guard.py` reuses the existing `interpretation_gate.Facet` three-valued enum,
`facet_bitset.FacetBitsetIndex` and `empirical_recognition.decide`. It does not
create a second serving or interpretation framework. `load_documents` verifies
operator pins and invokes the existing per-ID boundary gate for all 54 authorized
semantic-contract IDs **before** opening the combined documents artifact. Titles
are never parsed as semantic facts. All other 4,027 slots remain empty/unknown;
the 482 protected and 727 unknown identities remain title-only competitors.

The fixed input plan is pinned to
`950fcbe6cce0a7c3aad8ae93dcd792c3ac7aa8514688be5f0758bf19ff733ca8`;
the documents artifact is pinned to
`578dc19ba6b687071a5f1a54765b4537269bcf877aff153166c2b71bfa50cb1e`.
`audit.py` reproduces extraction coverage and span evidence using only those
permitted inputs. Derived facets are not a new statement authority.

Each extracted fact includes its field, exact character offsets, source span,
document-text SHA and rule ID. Contract records bind the normative authority SHA.
JSON-field spans may cover the whole serialized field, intentionally preserving
all supporting context instead of inventing substring offsets in decoded JSON.
Missing facts are UNKNOWN, not VIOLATED. Contradictory parsed facts are marked as
conflicts, never resolved by last-write-wins or model preference.

## Supported facets and measured extraction coverage

| Facet | Known contracts / 4,081 | Scope |
|---|---:|---|
| result_shape | 54 | Exact structured return types: integer, boolean, string, real, integer/string arrays, integer matrix |
| returned_entity | 4 | Explicit value versus index result roles |
| selection | 4 | Explicit all versus one selection clauses |
| graph_direction | 2 | Explicit structured directed/undirected domain |
| input_distinctness | 1 | Explicit structured `distinct: true`; no inference from titles |
| input_order | 2 | Explicit arbitrary versus rotated-sorted domain |
| output_alias | 1 | Explicit new output array |
| input_mutation | 0 | No mutation authority in supplied document fields; remains unknown |

Input-domain applicability uses inclusion, not indiscriminate inequality:
a contract accepting arbitrary array order also accepts sorted order. The strict
rotated-sorted domain includes sorted/full-rotation inputs **only when distinctness
is explicitly supplied**. A merely sorted or rotated-sorted description leaves
this inclusion UNKNOWN; it can allow duplicates. `Input array is strictly
ascending` and `Input elements are distinct` are narrow supported premises. An arbitrary-order
query is not covered by a sorted-only contract. A fresh output does **not** prove
that inputs are unmodified. Source agreement does not establish contract truth.

## Supported grammar versus unrestricted natural language

`parse_query` accepts anchored whole clauses separated by period, semicolon or
newline. Examples: `Return all indices. The graph is directed.`;
`Return one value`; `Input array is not necessarily sorted`;
`Do not mutate the input`; `Return a new array`; `Return an integer array`.
The complete fixed grammar is `QUERY_RULES`, with a test exercising every rule.
Negation, quotations, conditionals, disjunctions, unsupported wording and trailing
question marks are **not** normalized away. Unparsed spans are returned verbatim.
These are narrow descriptive clauses, not a claim to parse arbitrary language.

Even a fully parsed clause sequence is only a partial task specification. It does
not identify the intended algorithm, establish numeric bounds, or discharge
outside-catalogue interpretations. `filter_candidates` therefore preserves all
IDs for incomplete/conflicting grammar. For complete grammar it removes only
contradictory known facet records, retaining every unknown record. Bitset
exhaustiveness proves only finite filtering under these facts—not parser
soundness, open-world closure or recognition correctness.

## Fixed prospective composition and admission conditions

`guarded_decide` takes the existing complete canonical ranking, the original
threshold policy, existing exact retrieval service, and all contract slots.
It never reranks, substitutes a runner-up, or filters ranking by availability.

1. Missing/duplicate competitors or noncanonical rankings fail closed.
2. Conflicting query facts or explicit top-contract facet contradictions abstain.
3. Otherwise call the unchanged `empirical_recognition.decide`, including its
   truncation, cosine, margin, tie and dual-language exact-selection gates.
4. Return query evidence, unknown facets, and `semantic_proof=false` and
   `recognition_qualified=false`, including on empirical acceptance.

With unrestricted prose, extracted clauses are only empirical veto features:
the surrounding language may change their interpretation. Unknown facts do not
force acceptance or manufacture a premise. The adapter's acceptance is still
empirical and cannot establish applicability for arbitrary descriptions.
Do not expose this as a new production acceptance route until separately evaluated.

Prospective experiment: retain exactly the original **20-policy family**, same
IDs/cosine/margin values and selection criterion; compare each original policy
with its fixed v2 guard composition on the same authorized development split.
Do not add/tune grammar from old 52 development texts, use confirmation for
selection, or optimize threshold values here. Freeze this directory's code and
manifest before evaluation; preserve all original results. Report correct,
wrong-positive and control accepts, abstentions, parser coverage, contradiction
counts, unknown facets, and full latency separately. Any later grammar change
requires a new version and a new prospective freeze. No accuracy has been measured
in this lane; synthetic tests and contract coverage are not cohort results.

## Focused verification

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. timeout 60s bash -c '
  ulimit -v 524288
  python projects/algorithm_solver/catalogue/description-applicability-v2/audit.py
  python -m unittest discover -s projects/algorithm_solver/catalogue/description-applicability-v2 -p test_guard.py -v
'
```

Tests use owned synthetic clauses and synthetic service fixtures only. They cover
span provenance, all grammar rules, unknowns, negations/quotes/conditionals,
explicit oppositions, asymmetric input-domain inclusion, 4,081-slot retention,
boundary denial before opening payload, ranking validation, unchanged exact
retrieval projection, and no runner-up fallback. Mutation opposition is tested
synthetically, not asserted for any real contract. Existing acceptance gates,
source contracts, and protected reservations are unchanged.
