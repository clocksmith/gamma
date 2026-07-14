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

- `promotion-contract.v1.json`: target, comparator, population, metric,
  matched-lane, seed, human-review, and deployment-fidelity rules.
- `promotion-contract.schema.json`: executable structure for the contract.
- `data-license-catalog.v1.json`: current data lineage and license eligibility.
  An `unknown` license status blocks a source from the new campaign.
- `error-ledger.schema.json`: row-level diagnostic and adjudication envelope.
- `error-ledger.wmt13-nativekd2.v1.json`: deterministic diagnostic ledger built
  from the stored WMT13 predictions. It stores row indexes, hashes, signals,
  and artifact pointers rather than duplicating source, reference, or prediction
  text. Automated signals are not human labels.
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

## Required order

1. Preserve the current NativeKD2 BF16 baseline, freeze the Gamma-to-Doppler
   handoff format, and implement the import/parity machinery shared with
   Columbo. Do not select a translation winner.
2. Execute Columbo's independent Qwen 3.5 0.8B bridge, parity, selection,
   confirmation, promotion, registry approval, and governed export path.
3. Materialize and hash disjoint translation calibration,
   checkpoint-selection, seed-confirmation, and externally custodied promotion
   populations. Complete the license catalog and contamination audit first.
4. Complete the WMT13 diagnostic error ledger, then run the matched NativeKD2,
   verifier-filtered multi-teacher, router-sequence, and random-control lanes
   under identical initialization, exposure, update, ordering, decode, and
   seed rules.
5. Select the data recipe before opening the separate Gemma 3 1B versus Qwen
   3.5 0.8B base-model contract. Gamma then selects and freezes one BF16 winner
   using its population, seed, metric, guardrail, and human-review receipts.
6. Doppler imports that exact selected checkpoint and compares Q4K,
   selective-F16, and QAT artifacts derived from its identity.
7. Submit one committed hosted artifact to the externally custodied promotion
   population. A failed submission consumes the promotion look.

No artifact may be called promoted until every blocking field in
`promotionDecision.blockers` has a receipt and the terminal decision changes to
`passed` in a new immutable receipt.
