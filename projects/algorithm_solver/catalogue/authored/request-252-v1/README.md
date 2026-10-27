# Requested solution candidates: 252-ID disposition

This patch adds **68 original JavaScript/Python candidate pairs (136 source files)** for the supplied 252-ID list. Exact source base: `bc252ef318b165396288cd3f3d0ecbd4b84c03da`. It supplies source, reproducible development tests, and per-ID contracts, provenance, complexity and source hashes. It is not catalogue qualification or a claim that all 252 are implemented.

The [complete disposition](disposition.json) retains all 252 IDs and 504 requested language slots. **119 historical-reserved IDs remain closed; 65 exterior identities remain metadata-only.** The exterior group has 15 database and 50 ordinary-algorithm titles; title metadata does not authorize contract access. The [blocked CSV](blocked-disposition.csv) names every blocked ID and reason. No blocked statement, source or case payload was opened. Reservation release and exterior alias review/versioned access activation are separate owner decisions; no access policy was changed.

## Interfaces and evidence

Every JavaScript module exports `solve`; every Python module defines `solve`. Each batch manifest defines ordered parameters, result types, native API or JSON adapters, mutation/identity semantics, numeric limits and complexity. `TaskManager`, `Spreadsheet`, `Router` and `NeighborSum` remain available as native classes; problem 3217 also retains its identity-preserving linked-list function. Operation tapes and value-array adapters are explicit, not silently equivalent replacements for native APIs.

- [Batch 1](batch1/README.md): 17 pairs; [manifest](batch1/manifest.json).
- [Batch 2](batch2/README.md): 17 pairs; [manifest](batch2/manifest.json).
- [Batch 3](batch3/README.md): 17 pairs; [manifest](batch3/manifest.json).
- [Batch 4](batch4/README.md): 17 pairs; [manifest](batch4/manifest.json).

Tests distinguish public examples, independently derived bounded oracles, cross-language execution and selected numeric/maximum-shape checks. Additional [native-interface tests](review/test_native_interfaces.py) interleave independent class instances and check linked-list survivor identity. The high-risk independent review is under `review/`. [Integration evidence](INTEGRATION_VERIFICATION.json) binds final source hashes to the reported checks. Finite tests are not proof, hidden-judge acceptance, exhaustive maximum-domain certification, performance qualification or catalogue promotion.

All algorithms are newly authored, not copied solution dumps. Definitions are grounded in identity-bound official LeetCode pages; any public definition-only fallback and its license/provenance are identified in the batch records. Full statements/editorials are not redistributed. No private/protected cases, paid services, models or new dependencies were used.

## Applying this delivery

The downloadable cumulative patch contains all 68 new pairs and their evidence. Apply it once at the exact base above using `git apply --check` and then `git apply` from the repository root. This patch is scoped only to `projects/algorithm_solver/catalogue/authored/request-252-v1/` and makes no runtime/registry changes.

**The prior 244-pair request-506 delivery is already present byte-for-byte in this base**, imported by commit `e79744d75d0aad03bbdf8227dfd8e2146851e8b8`. Do not reapply the old patch on this base. This additive delivery leaves that work untouched. Across the two requests, the 758 unique IDs comprise 312 completed candidate pairs, 179 reserved IDs and 267 exterior identities; none becomes catalogue-qualified by this delivery.

No commit, push, deployment, reservation release or serving change was performed by this task.
