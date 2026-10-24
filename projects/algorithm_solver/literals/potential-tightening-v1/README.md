# Fixed-potential tightening cannot weaken the lifted bound

2026-10-24. [Item 53's proof](DRAFT.md) removes slack from old occurrence
penalties while preserving every suffix distance used by item 50. Every
activation weight weakly decreases, so every support-budget certificate is
at least as strong for the identical source universe and fixed potentials.
This guarantees neither a strict improvement nor a positive unrestricted bound.

An independent mathematical review confirmed the dominance argument and
narrowed its optimality statement: the construction maximizes the **fixed-L**
certificate within the Bellman-compatible family, or the exact dual among
assignments preserving the same actual suffix distances. Larger penalties
can increase actual path values; the broader dual optimum remains unresolved.
Finite old suffix distances, retained tight paths and identical feasible-entry
sets are explicit assumptions.

Three [invented oracle tests](test_proof.py) passed in 0.111 seconds. Across
32 small random source pairs, they compare old/full suffix distances and
occurrence weights, enumerate all eligible dictionaries of size at most four,
and check all corresponding support-budget charges and weak duality. Separate
fixtures show that reducing slack can leave the maximum charge unchanged and
that larger penalties can raise the actual path term. These small tests support
the algebra; they are not a corpus run, complexity measurement or production
implementation. The [oracle](proof.py) has no private loader or runner.

No item 28 or 50 private inputs were opened, no existing measured files changed,
and no new Gamma bound or witness was computed. A future matched experiment
requires a separately pinned implementation, invented complexity evidence,
bounded production and independent reporting, and Claude's freeze review.
Current-best selection, M1 thresholds and all owner gates remain unchanged.
