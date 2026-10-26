# Prospective contract-clause components — not a recognition policy

This new lane does not import/read the consumed confirmation, any cohort, model assets, source implementations, or previous decision outputs. Existing predictors remain frozen. No encoder/evaluation campaign is authorized here.

## Working components

`representation.py` checks live boundary authorization before opening an explicitly pinned structured authority artifact. The caller must supply the existing trusted boundary gate, not a permissive callback in production. Each clause has an exact field name, Unicode codepoint span **in that pinned JSON field value**, whole-field hash, authority hash, problem identity, role, explicit polarity and required flag. These are not invented offsets in a source webpage. Clause IDs hash this entire exact record; duplicate removal is exact identity only, not semantic/correlation equivalence. Structured annotations must themselves be independently checked against lawful authority before use. Current tests use synthetic fields only.

`aggregate.py` requires the complete unique rival population (default 4,081), raw scores, explicit query-evidence identities and role-scoped compatibility observations. It never removes title-only rivals. Unknown scope/polarity is ignored; conflicting annotations for the same evidence identity are UNKNOWN. Query evidence is an upstream **assertion**, not a claim that this module parses scope correctly. An actual adapter must carry independently checked query spans and must not mark embedding-derived polarity/scope explicit.

For each active query evidence identity and role, select the maximum supplied nonnegative predicate-compatibility value among that candidate's clauses. Opposite-polarity clauses tied at that maximum produce UNKNOWN. Otherwise multiply by query and contract polarity. Average over evidence identities within a role, then average over observed roles. This is an empirical compatibility signal, not entailment, probability, a contradiction proof or semantic satisfaction. No supplied observation means UNKNOWN. Required-role coverage records **observed comparisons**, never satisfied obligations. Near-paraphrase duplicate bias remains unresolved because exact identity is not semantic deduplication.

The returned ranking is still the original full-population raw-cosine ranking, with deterministic original-order ties. No new weight, threshold, margin, veto or acceptance rule is implemented. Signals are diagnostics until separately reviewed prospective integration. These components therefore cannot yet improve recognition or claim broader usefulness.

## Next review boundary

1. Independently review exact provenance, sign/conflict algebra and synthetic compositional properties.
2. Design one reusable adapter from already lawful contract fields and explicitly span-grounded query predicates. Existing frozen encoder may supply predicate compatibility only; embedding similarity is not entailment. Any normalization rule must be explicit and frozen, not inferred from this API's 0..1 validation.
3. Independently author a broader development population with role labels, natural-language paraphrases, compositions, scope/negation, equivalent alternatives and positive counterparts. Record actual author identities/exposure and sampling provenance; do not assume independence or use consumed confirmation examples. This step needs separate authority before acquisition/use.
4. Inspect factual extraction/observed-role reach on that new development evidence, and freeze one aggregation-to-ranking/acceptance proposal and baseline comparisons before any expensive evaluation. No training, new model assets, query whitelist, source-availability ranking filter or threshold sweep is authorized.

Synthetic tests cover exact spans, pre-open denial/tamper, composition/permutation, duplicates, polarity, conflicts, unknown scope/omission, finite scores, and full 4,081-rival preservation. They are software invariants, not natural-language accuracy evidence.

## Integration hardening successor

Authority loading reuses `public_batch_adapter.bounded_regular_read` after the live gate: anchored directory handles, no-follow regular files, bounded one-MiB default, FIFO/symlink/oversize rejection and mutation checks. Repository package root must be on PYTHONPATH. The aggregate dynamically loads its exact sibling representation file under a private module object, not the ambiguous global `representation` module. Required-clause IDs retain separate observed/unknown diagnostics even when several constraints share a role; observed means a supplied comparison only. No role aggregate can erase these per-clause UNKNOWN entries.
