# XML/content census and causal history comparison

The bounded gate is complete. This fixed split/history configuration loses to
unsplit Deflate despite a smaller archive than its shifted-history control.
The target remains **96,000,000 fully counted bytes**, with a **95,000,000-byte
stretch target**. This prefix earns zero objective credit.

## Population and byte ownership

The population is the previously exposed opening 250,000 raw bytes, SHA-256
`665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3`.
No confirmation sample or full corpus was read. The retained
[census](../results/xml_history250k_q0_v2/census.json) assigns every byte exactly
once and includes raw offsets for all lexical spans.

| Category | Raw bytes | Percent |
| --- | ---: | ---: |
| Outer XML syntax | 20,205 | 8.0820% |
| Metadata and bytes outside article text | 17,203 | 6.8812% |
| ASCII letter runs inside article text | 149,358 | 59.7432% |
| Wiki markup punctuation | 12,986 | 5.1944% |
| Entity spellings | 4,306 | 1.7224% |
| URLs | 6,951 | 2.7804% |
| Numbers | 2,918 | 1.1672% |
| Non-ASCII bytes inside article text | 1,381 | 0.5524% |
| Remaining article text, including whitespace | 34,692 | 13.8768% |
| Total | 250,000 | 100.0000% |

Outer XML/metadata is **14.9632%** and article-body bytes are **85.0368%**.
Including Wiki punctuation and entity spellings with structural material gives
21.88%, a different grouping. The working 25%/75% hypothesis needs a precise
definition and representative population. Article membership and ASCII letters
do not prove English prose; this classifier does not parse Wiki semantics or
identify language.

A page-local FIFO of 128 completed, exact ASCII words of length at least three
finds **753 metadata-to-text matches**, covering 4,983 destination bytes, among
23,199 eligible content words. It finds **zero reverse matches** among 577
eligible metadata words. Every donor precedes its destination. Common words
are included; these counts measure availability, not unique information or saved
bytes. Zero reverse matches applies only to this population and memory policy.

## Actual finite archives

All arms use Deflate6. P has one unsplit frame; other arms transmit XML/content
events capped at 4,096 raw bytes. Each event pays its label, raw length,
compressed length and termination. Dictionaries use only previously emitted
bytes. The [prospective plan](../operations/provenance/xml_history250k_q0_v2_plan.json)
fixes capacities, donor availability and the shifted control before execution.

| Arm | Meaning | Archive bytes | Savings versus B |
| --- | --- | ---: | ---: |
| P | Unsplit raw bytes | 86,703 | 55,746 |
| B | Separate histories within streams | 142,449 | 0 |
| K | Bookkeeping control, identical to B | 142,449 | 0 |
| X | XML history conditions text | 144,289 | -1,840 |
| E | Text history conditions XML | 146,174 | -3,725 |
| J | Both directions | 148,014 | -5,565 |
| S | Both directions with older opposite-stream donors | 148,487 | -6,038 |

J saves **473 bytes against S**: 386 text-payload bytes and 87 XML-payload bytes.
It loses **61,311 bytes against P**. The split pays 39,649 framing bytes for
4,404 events, versus 22 bytes for P; payloads also grow. The shifted donors have
equal capacity and opportunities but can remain topically related. This local
recency effect does not establish an improvement over unsplit coding.

This is not a replay of the stronger native parent. The 9,550-byte local codec
source gives J a source-plus-archive total of 157,564 bytes, excluding Python/zlib
delivery costs. That is not a qualified package score. No billion-byte forecast
is made. All seven ledger rows leave `program_size` and `hutter_score` unknown.

## Evidence and disposition

The [comparison](../results/xml_history250k_q0_v2/comparison.json) retains 21
process commands: independent encoding, decoding and raw re-encoding per arm.
All inverses, repeats, archive costs and common dictionary/event/output witnesses
agree. The witness does not claim zlib internal-state coverage. Independent
review rechecked every retained artifact identity.

The [guard](../run_logs/adaptive/20260919T210234Z_a3b1662116.resources/guard.json)
reports successful CPU 3 execution, cgroup peak 30,044,160 bytes, no violations
and completed owned cleanup. Admission bounded memory to 512 MiB, scratch to
64 MiB and wall time to 180 seconds. Timing is diagnostic. Taskset and sampled
affinity enforced CPU assignment; kernel cpuset delegation was unavailable.

The [canonical terminal](../operations/provenance/xml_history250k_q0_v2_terminal.json)
and [validated reflection](../operations/adaptive/reflections/20260919T210234Z_a3b1662116.json)
retire only this fixed segmentation/dictionary configuration. Seven arm rows
were appended through the terminal recorder, bound to the
[terminal index](../operations/provenance/xml_history250k_q0_v2_terminal_index.json).

Attempt v1 completed its codec phases but failed report publication by assuming
a file-backed zlib extension; this Python embeds zlib. Its
[failure reflection](../operations/adaptive/reflections/20260919T205853Z_08cac39226.json)
and bytes remain intact. V2 corrects runtime identity without changing codec
bytes or parameters. The codec group passed 60 tests; the additional runtime
identity regression and four architecture boundary checks passed after the fix.

The terminal reflection also
[validates under its original closure](../results/xml_history250k_q0_v2_verification_v2/verification.json)
in a read-only sandbox with the checkout unmounted. The first verification
attempt and its missing-schema failure are retained. The corrected verification
closure explicitly includes every schema the frozen validator's eager registry
loads, plus candidate revision payloads. It changes no experiment evidence and
grants no new execution authority.

## Next scientific question

Test a decoder-visible title/metadata-word specialist inside an unchanged native
parent event schedule, with explicit context and common-word controls. Select
opportunities by reference eligibility and parent bit cost, not raw byte fraction.
Verify the selected native parent's original closure before using its traces.
Freeze a new contract and any disjoint confirmation separately; this result
authorizes no automatic larger run.

The maintained adapter is
[xml_history_comparison_v2.py](../src/gamma_enwiki9/adapters/xml_history_comparison_v2.py).
The v1 adapter and entrypoint are frozen failed-attempt sources. Pure semantics
live in [xml_history_deflate_v1.py](../lib/coders/xml_history_deflate_v1.py).
The existing lab remains the operational entrance; component authority is preserved.
