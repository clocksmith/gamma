# Research Register Archive 017

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-10 - Full-score accounting q0 isolates one fixture-size error

Candidate `cmix_obias_full1g_submission_accounting_qm0_v1` matched every
frozen SHA-256 and all substantive arithmetic. It reproduced conservative
external and source-built conditional totals of `108,492,873` and
`108,501,365` bytes, respectively. Both remain below `109,685,196` and above
the active `105,000,000` target, with zero verified full-1G score credit.

The gate failed only because q0 froze the source-build decision size as
`6,790` rather than its actual `45,242` bytes; its frozen SHA-256 was correct.
One immutable q1 child may correct only that expected size and rerun all
identity, arithmetic, margin, and epistemic-boundary checks. Evidence: q0
decision, guard, and job `20260810T000550Z_139c3a4644`.

## 2026-08-10 - Conservative cmix-obias package boundaries are certified

Candidate `cmix_obias_full1g_submission_accounting_qm1_v1` corrected only the
q3 decision byte count and passed every frozen identity and arithmetic check.
Charging archive, compressor, head blob, and all `48` invocation bytes gives
`108,492,873` for the external form and `108,501,365` for the reproducible
source-built form if it produces the same full archive size.

Those boundaries sit `1,192,323` and `1,183,831` bytes below the current prize
ceiling, but `3,492,873` and `3,501,365` bytes above the active 105M objective.
They remain conditional: the external decode and source-built full encodes are
still active, so verified full-1G score stays unknown and score credit is zero.
Evidence: q1 decision, guard, and job `20260810T000738Z_5ab1801a01`.
