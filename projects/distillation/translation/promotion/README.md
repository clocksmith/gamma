# EN/ES single-student promotion contract

This directory owns Gamma's promotion target for the EN to Spanish and Spanish
to English translation student. It is a future promotion contract, not a
description of a promoted model.

The target is frozen in
[`promotion-contract.v1.json`](./promotion-contract.v1.json). The current
evidence establishes feasibility only:

- one Gemma 3 1B NativeKD2 checkpoint serves both directions without a router;
- its BF16 WMT13 diagnostic score is `34.1896` BLEU / `59.9388` chrF;
- Doppler produced an integrity-verified hosted Q4K artifact whose WMT13
  diagnostic score is `31.9149` BLEU / `58.2124` chrF; and
- NLLB-600M and M2M100-1.2B remain ahead on the visible WMT13 table.

WMT13 is diagnostic-only because its references and results influenced prior
data, checkpoint, decode, and router selection. It cannot select or promote a
candidate under this contract.

The current NativeKD2 BF16 checkpoint is frozen only as a reproducible
baseline. Doppler's trainer-handoff contract binds its weights, tokenizer,
architecture, conversion lineage, and diagnostic evaluation inputs. It is not
a selected candidate or winner. Only Gamma may select the BF16 winner after
the matched campaign, declared seeds, and blocking human review complete.

## Contract artifacts

- `exposure-ledger.v1.json`: append-only, hash-chained chronology that records
  WMT13 exclusively as development evidence and pins the shared Clocksmith
  schema digest. Promotion readiness verifies this ledger before evaluating
  later gates.
- `promotion-contract.v1.json`: target, comparator, population, metric,
  matched-lane, seed, human-review, and deployment-fidelity rules.
- `promotion-contract.schema.json`: executable structure for the contract.
- `human-review-contract.v1.json`: frozen blocking review protocol. It fixes
  blinding, reviewer qualification, adjudication, population floors, a paired
  exact sign test with Holm correction, direction/domain non-regression, and
  critical-error guardrails before any review population is materialized.
- `human-review-contract.schema.json`: executable structure for the review
  protocol.
- `population-procurement-contract.v1.json`: frozen row counts, content mix,
  native-source/reference rules, role separation, rights, contamination, and
  custody requirements for calibration, selection, confirmation, and the
  one-use promotion population. It is a procurement specification; every role
  remains unmaterialized.
- `population-procurement-contract.schema.json`: executable structure for the
  procurement specification.
- `data-license-catalog.v1.json`: current data lineage and license eligibility.
  Any status other than `verified` blocks a source from the new campaign. The
  catalog now binds exact candidate revisions for MASSIVE 1.0, TICO-19, and
  FLORES+ across conversational, medical, and general-informational domains.
  They remain ineligible pending human approval, role assignment, and the
  recorded source-specific audits.
- `public-source-candidate-verification-2026-07-14.json`: network replay receipt
  for the exact MASSIVE archive and bound EN/ES files, TICO-19 files, and
  FLORES+ revision/gating metadata. Its pass is source-identity-only and grants
  no campaign eligibility.
- `error-ledger.schema.json`: row-level diagnostic and adjudication envelope.
- `error-ledger.wmt13-nativekd2.v1.json`: deterministic diagnostic ledger built
  from the stored WMT13 predictions. It stores row indexes, hashes, signals,
  and artifact pointers rather than duplicating source, reference, or prediction
  text. Automated signals are not human labels. Human disposition is required
  separately for the input/reference and for every compared system; a generic
  row label cannot satisfy the gate.
- `promotion-readiness.v1.json`: deterministic denial receipt for the current
  repository state. It records the population, license, human-review, run-
  contract, selection, and promotion blockers without declaring a winner.
- `upstream-model-identity-verification-2026-07-13.json`: official upstream
  API verification for every pinned comparator, base-model candidate, and
  COMET checkpoint revision used by the contract.

Run the fail-closed gate with:

```bash
python3 projects/distillation/translation/pipeline/check_translation_promotion_readiness.py
```

Use `--allow-blocked` only when refreshing an audit receipt. It does not grant
training, selection, artifact competition, or promotion authority.

Evaluate a completed blinded review ledger with:

```bash
python3 projects/distillation/translation/pipeline/evaluate_translation_human_review.py REVIEW_LEDGER.json
```

The evaluator maps custodied A/B assignments only after adjudication, verifies
the complete item-by-comparator matrix, applies the frozen paired test and Holm
family, checks every direction/domain stratum, and emits a hashed pass or fail
receipt. It never substitutes automatic scores for missing human dispositions.

The three public source candidates are not the sealed promotion population.
FLORES+ is explicitly gated to protect evaluation integrity, while TICO-19 and
MASSIVE are public. They may support pre-promotion roles only after admission.
The promotion population must contain newly commissioned or otherwise
inaccessible, licensed material held by the external custodian and must remain
unavailable to trainers, selectors, and ordinary agent workspaces.

Replay public source identity verification with:

```bash
python3 projects/distillation/translation/pipeline/verify_translation_data_sources.py
```

Build the diagnostic human-review package only from a custodian-owned secret:

```bash
python3 projects/distillation/translation/pipeline/build_translation_error_review_package.py \
  --ledger projects/distillation/translation/promotion/error-ledger.wmt13-nativekd2.v1.json \
  --blinding-key /CUSTODY/blinding-key.bin \
  --worklist-id gamma-translation-wmt13-diagnostic-review-v1 \
  --out-worklist /REVIEWER/worklist.json \
  --out-mapping /CUSTODY/system-mapping.json
```

The reviewer worklist contains source, reference, and randomized output labels
but no system identities or automated signals. The separately written mapping
is mode `0600`, binds every prediction hash, and must remain unavailable to
reviewers. Two qualified reviewers and a distinct adjudicator must complete the
per-system ledger; no agent may synthesize those human dispositions.

After both reviewer submissions and the distinct adjudicator submission bind
the same worklist, the custodian merges them with:

```bash
python3 projects/distillation/translation/pipeline/merge_translation_error_review.py \
  --ledger projects/distillation/translation/promotion/error-ledger.wmt13-nativekd2.v1.json \
  --worklist /REVIEWER/worklist.json \
  --mapping /CUSTODY/system-mapping.json \
  --reviewer /CUSTODY/reviewer-one.json \
  --reviewer /CUSTODY/reviewer-two.json \
  --adjudicator /CUSTODY/adjudicator.json \
  --out /CUSTODY/error-ledger.adjudicated.json
```

The merge rejects missing rows or outputs, duplicate actors, an adjudicator who
is also a reviewer, unsupported labels, missing evidence, tampered receipts,
and an adjudication that does not bind both reviewer submission hashes.

The receipt reports blockers separately for matched training, checkpoint
selection, BF16 winner declaration, Doppler artifact competition, and promotion
submission. Outcome evidence such as matched-lane receipts, seed confirmation,
or a Gamma winner receipt cannot circularly block the training phase that must
produce it. Population, license, contamination, human-review-rule, error-ledger,
and matched-run-contract blockers still fail closed before training.

## Required order

1. Preserve the current NativeKD2 BF16 baseline, freeze the Gamma-to-Doppler
   handoff format, and implement generic import/parity machinery. Do not select
   a translation winner.
2. Materialize and hash disjoint translation calibration,
   checkpoint-selection, seed-confirmation, and externally custodied promotion
   populations. Complete the license catalog and contamination audit first.
3. Complete the WMT13 diagnostic error ledger, then run the matched NativeKD2,
   verifier-filtered multi-teacher, router-sequence, and random-control lanes
   under identical initialization, exposure, update, ordering, decode, and
   seed rules.
4. Select the data recipe before opening the separate Gemma 3 1B versus Qwen
   3.5 0.8B base-model contract. Gamma then selects and freezes one BF16 winner
   using its population, seed, metric, guardrail, and human-review receipts.
5. Doppler imports that exact selected checkpoint and compares Q4K,
   selective-F16, and QAT artifacts derived from its identity.
6. Submit one committed hosted artifact to the externally custodied promotion
   population. A failed submission consumes the promotion look.

No artifact may be called promoted until every blocking field in
`promotionDecision.blockers` has a receipt and the terminal decision changes to
`passed` in a new immutable receipt.
