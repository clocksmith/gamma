# facet-gate-dev-128-v1: frozen development candidate for the two wrong 1b acceptances

## Owner direction

Owner direction of 2026-10-23, relayed from Mars: fix the two wrong recognition acceptances as a
separate correctness task, and do not wait for compactness. This is gamma-team board item B
(claude).

## The two failures and the earlier attempt

The [consumed fresh result](../recognition-fresh-suby-v1/README.md) was 16/36 correct, with
**two wrong acceptances** and 18 abstentions. The
[diagnosis](../post-fresh-diagnosis-suby-v1/README.md) found two failures, both a missing
answer-changing distinction:
- **Trade count:** the stock request omitted how many trades are allowed (fees and cooldown
  were excluded). The route returned the cooldown source.
- **Duplicates:** the kth-largest request omitted whether duplicates count. The route returned
  the duplicate-counting source.

The earlier [required-facet candidate](../required-facets-dev-128-v1/README.md) did abstain on
these patterns, but it
[lost all 7 control-correct development answers](../required-facets-real-dev-128-v1/README.md):
- six of them because their sources had no contract;
- one because its output phrase was suppressed as uncertain, on a facet that does not separate
  any stock sources.

The consumed fresh 36 are not replayed or reused here in any form.

## Candidate

It is opt-in and changes no default route, approval manifest or historical receipt.

| File | SHA-256 |
| --- | --- |
| [algsolve/facet_gate.py](../../algsolve/facet_gate.py) (gate and grammar) | `e807169d958d492ad7f1b6774ad9b6e24dda5a42415d3f1b0def5ed188f68d46` |
| [contracts/facet_gate_dev_128_v1.json](../../contracts/facet_gate_dev_128_v1.json) (66 contracts, written by [declarations.py](declarations.py)) | `467bddcf823f0c84120c059776260200fc3075a313ce87ef208e301a8ec3a3f0` |
| [compare_real.py](compare_real.py) (real-route driver) | `0196d317749517ec36808bda2ff616f8f9795196118b42e5ec7fca8869effdb7` |
| [synthetic.py](synthetic.py) | `6043a04b155cfb09a8a3abd1d2aaf8bd1ec1e708a6e129975f2630ffba6279ad` |
| [declarations.py](declarations.py) | `640042a29be30953861ff293e000bb529b53e7d5b42b33a3364bfc35cab3f9df` |
| [tests/test_facet_gate.py](../../tests/test_facet_gate.py) | `4311f1e3db0c58c1dd1286f7f40e07ff15d2cc608b59294dfcc3e912ea9d649f` |

### Rules

1. **Placement.** The gate runs after the existing identity check, and only for a non-exact
   stored answer. The exact-statement route, numeric thresholds, sibling margin, source
   approval and public execution are unchanged. A rejection abstains. The selected source is
   never replaced by a lower-ranked one.
2. **Contracts.** Every one of the 66 indexed sources has a contract. Each one records:
   - its family;
   - the facts that separate it from same-family siblings, or from a material alternative
     reading;
   - its required facets.

   Sources with no such distinction declare none, as a reviewed statement. A source with no
   contract still abstains, for example a stale or new source.
3. **Required facets** are only those that change the answer within the family:
   - stock: trade count, fee and cooldown;
   - rank: output, duplicates, stream;
   - islands: output, border, shape transform, cell change;
   - and so on per family; the full table is in [declarations.py](declarations.py).

   Output is not required for stock, because every stock source returns profit. That removes the
   earlier loss of stock-repeat.
4. **Settling a required facet.** A required facet is settled either by certain, explicit query
   evidence for the source's value, or, only for a declared add-on feature, by the request never
   mentioning that feature. The add-on features are:
   - fee and cooldown;
   - circular layout and one deletion;
   - infinite repetition;
   - grid border, shape transform and cell change;
   - stream updates;
   - sorted input and one-based indexing.

   Trade count, duplicate policy and output never default, and the gate refuses a contract
   document that tries to give them a default. A mention the grammar cannot read blocks the
   default, as in "if there is a fee, it is per trade". Source facts, public examples and the
   absence of a sibling never fill an omission.
5. **Abstention reasons.**
   - **Contradiction:** a query fact contradicts a declared fact. Sorted input is compatible with
     an arbitrary-order source.
   - **Conflict:** two certain values for a declared facet.
   - **Uncertain:** only hedged, conditional, quoted or adjacent-`or` evidence for a required
     facet.
6. **Grammar.** A conservative phrase grammar, separate from the approval-bound
   `requirements.py`. Uncertainty is clause-scoped:
   - a hedge or conditional before the phrase in its clause, or a sentence opening with a
     conditional;
   - an `or`/`nor` within two words of the phrase.

   These are not uncertainty:
   - a recognized absence list such as `no fees or cooldown`;
   - a trailing fallback such as `or zero`;
   - permission words (may, can, could).

## Development evidence so far (developer-exposed, in-sample)

- **Grammar:** written with the 16 specified retained development statements visible, and their
  wording informed it. All 16 pass the gate for their expected source. This is in-sample.
- **[synthetic.py](synthetic.py):** 40 requests written by me, giving 84 decisions against real
  index contracts, with no retrieval. They include both failure patterns in new wording and
  near-sibling confusions in every declared family. All 56 must-abstain decisions abstain and all
  28 must-accept decisions accept ([synthetic.json](synthetic.json)). The cases were written
  while building the grammar, so this is a software-behavior check, not recognition evidence.
- **Unit tests:** 13 in [tests/test_facet_gate.py](../../tests/test_facet_gate.py), passing with
  the existing required-facet, requirement-filter and requirements tests (33 in total).
- **Judge and lane checks:** 37 passed.

## Frozen run: real-route development comparison

This uses the same protocol as required-facets-real-dev-128-v1, with only the candidate arm
changed.

**Inputs:**
- the retained `recognition-rebuild-dev-suby-v1` control: 66 sources, cached source vectors,
  24 requests, the original approval catalog and the unchanged thresholds;
- the 128 encoder in place, with weights, tokenizer and config hashed.

**Runtime.** `runs/facet-gate-approval-runtime-128-v1` is a copy of the earlier isolated
approved runtime plus `facet_gate.py`; all 96 approval bindings verify.

**Procedure.**
- Control and candidate each do their own real embedding and retrieval, in alternating order.
- The run asserts identical vectors and candidates per pair.
- All decisions are sealed before source-test scoring.
- Limits: 4 CPU threads, 8 GiB, 400% CPU (systemd scope), and 900 s.

**Predictions:**
- **F1:** the control reproduces every historical disposition: 7 correct, 0 wrong, no drift.
- **F2:** the candidate keeps all 7 control-correct answers, with 0 wrong acceptances.
- **F3:** the candidate answers nothing the control abstains on. The gate only rejects.
- **F4:** retrieval is identical within every pair.
- **F5:** the 8 requests without public examples stop before retrieval in both arms.

**Readiness rule (frozen).** The candidate is ready for independent confirmation only if F2
holds (0 lost, 0 wrong) and the synthetic suite stays all-pass on the frozen files. Otherwise it
stays unselected, and the failure is recorded without tuning on this cohort.

## Confirmation: owner gate (not done here)

This development set has no materially ambiguous request with an indexed answer, so it cannot
show that the two failures are fixed on real inputs. Only an independently authored set can.

Confirmation needs a new, independently authored, reviewed and unopened request set, with
authors other than me. It needs:
- materially ambiguous requests in the declared families;
- complete requests in those families;
- requests on undeclared sources.

It also needs its own freeze before anyone sees it. I stop at that point and record it on the
board as waiting on the owner.

## Not claimed

- No promotion and no 1b qualification.
- No change to the 1a gates or the full-catalog absence gate.
- No training, downloads, protected composition data or fresh-36 replay.
- The contracts are implementer declarations pending review. They are necessary conditions, not
  semantic equivalence.
