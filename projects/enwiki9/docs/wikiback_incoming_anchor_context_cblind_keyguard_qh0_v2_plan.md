# WIKIBACK Cblind Title-Key Guard QH0 v2

Candidate ID: `wikiback_incoming_anchor_context_cblind_keyguard_qh0_v2`

Parent: `wikiback_incoming_anchor_context_qh0_v1`

Status: source-correction child, zero score credit. The parent job was
cancelled before launch because its blind control could not prove the frozen
unrelated-title invariant. This is not a scientific rejection of WIKIBACK.

## Inherited contract

Except for the changes below, inherit the population, exact inputs, parser,
Wfull/Cprior/Ctarget construction, finite Q24 side coder, residual coder,
framing, source ceiling, chronological splits, exactness requirements,
economics, promotion gate, and kill condition from
`docs/wikiback_incoming_anchor_context_qh0_plan.md`.

The existing recovered dictionary and inverse backend remain the bound runtime
inputs. The gate remains an opening-10M trace-level experiment and receives no
forecast credit.

## Corrected Cblind invariant

The parent stored completed blind-control rows as:

```text
(page_ordinal, snapshot)
```

That cannot prove that a chosen source has a normalized title key distinct
from the current title. Opening 10M contains 46 repeated normalized title keys
covering 92 title rows, so ordinal inequality is not key inequality.

Version 2 stores:

```text
(page_ordinal, normalized_title_key, snapshot)
```

Before support matching, Cblind removes every row satisfying:

```text
source_title_key == current_title_key
```

It then applies the unchanged capacity, nearest unique-count bit-length, and
earliest-ordinal selection rule. Every selected source must satisfy an explicit
key-inequality assertion. Page-wide deactivation remains unchanged when a
distinct-key blind source or Cprior cannot supply Wfull's unique count.

The source wrapper configuration is idempotent: repeated same-process
preflight and entry-point calls must not duplicate or change the counted source
file list, config bytes, or source allowance.

## Additional exact receipts

Bind into the machine digest:

- every completed source ordinal and normalized title key;
- every Cblind query's current title key and reference support;
- every same-key source ordinal and key excluded before support matching;
- every selected source ordinal and normalized title key;
- selected-source count and selected-source key-violation count.

Require repeated encoder and decoder machine receipts to agree exactly and:

```text
Cblind selected source count                 > 0
Cblind selected source key violations        == 0
Cblind key-guard replay                       exact
Cblind query and selection digests            identical
```

These conditions enter the causal/exact gate. A violation is malformed
evidence, not a compression rejection. Missing receipts, an unexercised blind
selector, malformed digests, unequal query or selection digests, or an
unexpected encoder/decoder receipt count must raise and exit nonzero before a
scientific `REJECT` or `AUTHORIZED_DISTANT_REPLAY` can be published. The
wrapper suppresses the inherited v1 verdict until validation; a failure
atomically replaces the provisional decision with `MALFORMED_EVIDENCE`, a null
scientific verdict, and all authorizations false before raising.

## Versioned artifacts

Use distinct identities:

```text
frame magic       WIKIBK2
config schema     wikiback_incoming_anchor_context_config_v2
decision schema   wikiback_incoming_anchor_context_qh0_decision_v2
tool              tools/wikiback_incoming_anchor_context_cblind_keyguard_qh0_v2.py
result            results/wikiback_incoming_anchor_context_cblind_keyguard_qh0_v2/
```

The counted source bundle includes this delta plan and wrapper, the preserved
v1 plan and implementation used as the common codec substrate, and every
direct donor already charged by v1.

## Execution order

Do not launch while NNCP owns `/tmp/enwiki9-heavy.lock`. After NNCP reaches a
terminal receipt, re-run the source/input/output preflight and enqueue or run
exactly one candidate-specific v2 adaptive job. Do not requeue v1.
