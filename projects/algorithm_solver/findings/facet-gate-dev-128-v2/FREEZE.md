# facet-gate-dev-128-v2: frozen strict development candidate for the two wrong 1b acceptances

## Why a v2

This is gamma-team board item B (claude), from the owner direction of 2026-10-23: fix the two
wrong recognition acceptances as a separate correctness task.

[v1](../facet-gate-dev-128-v1/FREEZE.md) (`0ba7d8c0a`) was superseded before it ran.
[Its note](../facet-gate-dev-128-v1/NOTE-2026-10-23.md) records why. Codex's review (team LOG,
17:23Z and 17:26Z, 2026-10-23) raised three objections, all accepted here:
1. **Absence defaults** let silence, or a non-match of the phrase grammar, settle an
   answer-changing facet. A nested negation ("it is not true that there are no fees") was read
   as a no-fee fact.
2. **Empty required-facet lists** were justified by "no same-interface sibling". This recreates
   the rank failure, where the material alternative reading had no indexed source.
3. **The driver** recorded the hashes of the files it ran but never checked them against the
   frozen ones.

The two failures are unchanged. In the [consumed fresh result](../recognition-fresh-suby-v1/README.md):
- a stock request omitted the trade count, and the cooldown source was returned;
- a kth-largest request omitted the duplicate policy, and the duplicate-counting source was
  returned.

The consumed fresh 36 are not replayed or reused in any form.

## Candidate S (strict) and ablation D

The gate is [algsolve/facet_gate.py](../../algsolve/facet_gate.py). Both arms use the same gate
code and the same 66 contracts, written by [declarations.py](declarations.py).

| Arm | Contract document | `absence_defaults` | Role |
| --- | --- | --- | --- |
| **S** | [facet_gate_dev_128_v2_strict.json](../../contracts/facet_gate_dev_128_v2_strict.json) | none | **the candidate** |
| D | [facet_gate_dev_128_v2_defaults.json](../../contracts/facet_gate_dev_128_v2_defaults.json) | 11 add-on features | ablation measuring the coverage cost of strictness. **Never eligible for confirmation**: synthetic cases show it accepting unreadable add-on paraphrases. |

### Rules

1. **Placement.** The gate runs after the existing identity check, only for a non-exact stored
   answer. The exact route, thresholds, sibling margin, approval and public execution are
   unchanged. A rejection abstains, and the selected source is never replaced.
2. **Completeness.** A source is `reviewed` only when its answer-changing facets were checked
   against same-family siblings *and* against material alternative readings that have no indexed
   source. 19 of the 66 sources are reviewed:
   - the 6 stock sources;
   - kth largest and rank transform;
   - house robber I and II;
   - two-sum I and II;
   - course schedule I and II;
   - number of islands and max area;
   - top-k frequent;
   - minimum-size window;
   - maximum subarray.

   Every other source is `unreviewed` and abstains (`facet_gate_unreviewed_source`). An empty
   list is not treated as proof.
3. **Facets the review found.** Besides the sibling distinctions, the review found these
   answer-changing facets:
   - holding one share (stock with more than one trade);
   - adjacency (houses);
   - 4-connectivity (islands; the diagonal reading has no indexed source);
   - border;
   - exactly one solution and distinct positions (two-sum);
   - prerequisite direction (course order);
   - unique answer and any order (top-k);
   - positivity, the at-least relation, the zero fallback and no repetition (minimum window);
   - nonempty, non-circular and no deletion (maximum subarray);
   - the rank base (rank transform).
4. **S settles a required facet only by certain, explicit query evidence** for the source's
   value. Silence is never evidence.
5. **D additionally settles 11 add-on features by silence**: fee, cooldown, layout, deletion,
   repetition, border, transform, cell change, stream, sorted input and one-based indexing.
   This applies only when the request never mentions the feature at all. A document cannot
   default trade count, duplicates, output or any other no-default facet.
6. **Uncertainty (both arms):**
   - a hedge or conditional before the phrase in its clause, or a sentence opening with a
     conditional;
   - quotation;
   - an `or`/`nor` within two words. Absence lists ("no fees or cooldown") and trailing fallbacks
     ("or zero") are not alternatives;
   - an absence phrase under a negation that scopes over it ("not true that", "false that", or
     "not" right before it).

   Contradictions and conflicts abstain, as in v1.
7. **Pre-run check.** [compare_real.py](compare_real.py) checks every file named in
   [manifest.json](manifest.json) before any inference, including the isolated runtime's copy of
   the gate.

## Development evidence before the freeze (developer-exposed, in-sample)

- **Grammar.** It was written with the 16 specified retained development statements visible.
  Against their expected sources, the offline gate checks give:
  - **S** accepts 12 of 16. It rejects:
    - stock-once (fee and cooldown unstated);
    - islands-area (border and cell change unstated);
    - short-positive-window (repetition unstated);
    - best-sum-window (layout and deletion unstated).
  - **D** accepts 16 of 16.
- **[synthetic.py](synthetic.py).** 39 requests and 63 decisions, against the real contracts
  with no retrieval ([synthetic.json](synthetic.json)). They include:
  - both failure patterns in new wording;
  - Codex's two counterexamples;
  - unreadable add-on paraphrases;
  - diagonal, empty-subarray and multiple-pair readings;
  - unreviewed sources.

  | Arm | Mismatches | Wrong acceptances | Accepted |
  | --- | ---: | ---: | ---: |
  | S | 0 | 0 | 18 |
  | D | 0 | 2 (the cooldown and circular-street paraphrases, by design) | 23 |

  I wrote the cases while building the grammar, apart from Codex's two, so this is a software
  check.
- **Unit tests:** 16 in [tests/test_facet_gate.py](../../tests/test_facet_gate.py), passing with
  the existing required-facet, filter and requirements tests (41 in total). The judge and lane
  checks pass (37).

## Frozen run: real-route development comparison

**Inputs.** The retained `recognition-rebuild-dev-suby-v1` control:
- 66 sources and cached source vectors;
- 24 requests;
- the original approval catalog and unchanged thresholds;
- the 128 encoder in place, with its files hashed.

**Runtime.** `runs/facet-gate-approval-runtime-128-v2` is a copy of the earlier isolated
approved runtime plus `facet_gate.py`. Its 96 approval bindings verify at launch.

**Procedure.**
- The three arms run in rotating order (control, S, D).
- Each does its own real embedding and retrieval, and identical vectors and candidates are
  asserted for every request.
- Decisions are sealed before source-test scoring.
- Limits: a systemd scope at 8 GiB and 400% CPU, 4 threads, 900 s.

**Predictions:**
- **F1:** the control reproduces its historical dispositions: 7 correct, 0 wrong, no drift.
- **F2:** S makes 0 wrong acceptances. It keeps exactly 5 of the 7 control-correct answers, and
  loses short-positive-window and best-sum-window, which leave add-ons unstated.
- **F3:** D makes 0 wrong acceptances and keeps all 7.
- **F4:** neither gated arm answers a request the control abstains on.
- **F5:** retrieval is identical across the three arms for every request.
- **F6:** the 8 requests without public examples stop before retrieval in all arms.

**Readiness rule (frozen).** S is ready for independent confirmation only if all of the
following hold:
- S has 0 wrong acceptances on this run;
- F4 holds;
- the frozen synthetic suite shows 0 S mismatches and 0 S wrong acceptances.

Coverage is reported with no threshold, and coverage losses are kept as results. D is never
eligible. A failure is recorded without tuning on this cohort.

## Confirmation: owner gate (not done here)

This development set has no materially ambiguous request with an indexed answer, so it cannot
show that the two failures are fixed on real inputs. Confirmation needs:
- a new, independently authored, reviewed and unopened request set, with authors other than me;
- materially ambiguous requests in the reviewed families;
- complete requests in those families;
- requests whose best source is unreviewed;
- its own freeze before anyone sees it.

I stop there and record it on the board as waiting on the owner.

## Not claimed

- No promotion and no 1b qualification.
- No change to the 1a or full-catalog absence gates.
- No training, downloads, protected data or fresh-36 replay.
- The contracts are implementer declarations under review. They are necessary conditions, not
  semantic equivalence.
