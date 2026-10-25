# Conservative interpretation refinement (prospective mechanism)

This module applies the owner's mathematical repair to the recognition boundary.
It is **not** an informal-language analyzer, completeness certificate, production
recognizer, or claim that goal 1b is achieved. Existing calibrated historical
recognition results remain unchanged.

## Rule and trust boundary

A separately trusted analyzer must supply a sound overapproximation of **all**
interpretations compatible with a query, including an outside-catalogue
possibility. Each candidate's facets have three explicit values: satisfied,
violated, unknown. Only a sound violated verdict can remove a possibility;
unknown/missing facets remain. A singleton can support identity selection only
when outside-catalogue ambiguity is also excluded by the trusted analysis.
An empty envelope abstains rather than accepting through vacuous reasoning.

The dataclass's hashes bind query, universe and analysis contract; hashes do not
prove the analysis sound. Its constructor is not a security/authentication
boundary. These are internal trusted-analysis objects, **never request fields**.
No production producer is certified or wired in. An embedding score, top-k list,
margin, self-reported `complete` flag or typed assertion cannot supply missing
completeness. The existing post-recognition bridge remains a metadata mechanism,
not a semantic-uniqueness proof.

## Tested consequences

- A retrieved transaction-limited candidate does not erase an omitted unlimited-
  transaction interpretation when the query leaves that facet unknown.
- A catalogue singleton still abstains while an outside interpretation remains.
- Sound refinement only removes identities and never reintroduces outside risk.
- Conditional singleton results retain exact analysis/query/universe bindings.
- Eight synthetic controls include all 81 three-candidate/outside facet settings.

This preserves the attachment's distinction between logical soundness under
complete premises and statistical conditional error under independent calibration.
Zero observed errors on these synthetic controls establishes neither a population
risk bound nor zero-error recognition. Source availability and implementation
language must never break an identity ambiguity.

The optimizer already uses exact `(selection_count, singleton_count)` ordering
and retains qualified source variants. Finite oracle checks remain finite evidence;
no small-bound equivalence theorem, complete maximal-repeat pricing, general-DAG
exact-inference theorem, or universal generalization claim is introduced here.
