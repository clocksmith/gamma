# Completed checkpoint dependency inventory

This checkpoint integrates completed groups, not the pending Hard3/Hard4 campaigns.
No private source copies, imported tests, catalogue records, model weights or raw judge observations belong in this public inventory.

| Lane | Frozen identity | Actual outcome | Adoption |
|---|---|---|---|
| Hard2 original | `482992d29fc549561fa236e01661844bc06a9963b4af66d9fd2c72e8263439fb` | Original14-pair run retained;1515 rounded decimal conversion not sound authority | Not used; old lane deliberately unregistered |
| Hard2 numeric-v2 | `72a1398bc6d4c75bd08222b63420bdc42c45198002ae58b547227f2e8ca3ee33` | Fresh14/14,6228 checks,246 calls; independent original-raw replay also passed | v17; exact authority and service summary |
| Medium2 original | `52a326bd04dd3d8e1e72373127e94d2cecf00ef09413727c9371d8125f3df235` |15/16,21240/21272 checks,676 calls; JS1743 heap failure | v18 adopts15 passing original sources; failure retained |
| Medium2 packed source | `ebeb7f8a9e831ef98daf259c0c93ba51e87ebd99efc8d93390511345271fc6b9` | Same15/16 and same JS1743 failed batch | No successful repaired-source adoption |
| Medium3 | `0497760fa258ca59e67e24d6b076bada9cc4432ed52b69a1cd4ae2f354be6bf6` |16/16,3096 checks,114 calls | v19 |
| Medium4 | `8b7f450b1c7ac3df86a2d3685b1e71d9e31d9825594b9cc9437b9ccf6846bb87` |16/16,2854 checks,98 calls | v20 |

## Code and evidence dependencies

- Each fixed lane supplies its own pinned `qualify.py`, `verify.py`, `oracle.py`, `cases.py`, harnesses, host/transport tests and public contract/semantics sidecars. Source input remains the existing owner-authored `authored/leetcode-{hard,medium}32-v1` tree; no imported source is copied by the summaries.
- The sole changed candidate in these groups is separately attributed `authored/packed-path1743-v1/javascript/1743.js`. Its native failure is retained; the original owner source is untouched.
- `catalogue/public_batch_adapter.py` registers fixed exact populations and observation policies, guards no-follow bounded reads, independently replays actual observations and only adopts passing pairs. Its test module rejects cross-lane numeric/property relaxation. Corrected1515 policy is limited to the seven-ID numeric-v2 lane; Medium3 is scalar-only, Medium4 scalar/list.
- Operator authority binds reviewed official identities/domains, ordered arguments, results, derived complexity and explicitly local effects. `ADOPTION-AUTHORITY-v1.json` copies that reviewed metadata; it does not grant source-publication rights or substitute for actual native verification.
- `QUALIFICATION-RESULT-v1.json` files contain aggregate IDs/hashes/counts and failure classifications only. `SERVICE-INTEGRATION-v1.json` files bind actual staged service readbacks; they do not expose the private catalogue/receipts or mean current candidate execution is qualified.
- Historical negative receipts/freezes remain unchanged. Later summaries/README sections explicitly supersede earlier preparation-only labels without rewriting those records.

At v20 the authoritative full4081/8162-slot inventory reports502 JS and503 Python qualified artifacts. Protected482 and unknown727 boundaries remain closed. Complete R1 coverage, informal1b recognition, current runtime serving1c and historical compact-library M1 remain unqualified.
