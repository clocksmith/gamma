# Development-only donor coverage attribution

The proposed retrieval transfer does not pay on the declared development data.
Searching the same retained pool finds additional donors, but those opportunities
have little cost left under FX2 and the tested continuations make prediction worse.
This closes a bounded selection diagnostic, not the broader cross-history idea.

Candidate `fx2_donor_coverage250k_q0_v1`, source `b860b886c`, job
`20260920T185146Z_aebb847936`, completed 2026-09-20 at 18:52:24 UTC.
The [frozen plan](../operations/provenance/fx2_donor_coverage250k_q0_v1_plan.json),
[comparison](../results/fx2_donor_coverage250k_q0_v1/comparison.json),
[independent cost checks](../results/fx2_donor_coverage250k_q0_v1/verification.json)
and [validated reflection](../operations/adaptive/reflections/20260920T185146Z_aebb847936.json)
are authoritative for this scope. Imports and measured parent sources are unchanged.

## Controlled comparison

Only the retained development population was opened: raw `[0,250000)`, represented
by 151,210 WRT bytes and 1,209,680 binary predictions. Validation and confirmation
were not used. The original parent probabilities, truths, initialization, update
schedule, dictionary, parser and histories are fixed. No training or codec run.

The sealed v2 implementation supplies exact decoded prefixes and completed donor
records. All arms use its FIFO capacity of 64 words per role, 32 modeled/64 raw
bytes per word, and 4,096-modeled-byte frozen epochs. The selectors are:

1. **Early four:** the original first four eligible paired right donors.
2. **All paired:** continue the identical greedy pairing beyond four donors.
3. **Full pool:** search every retained donor, including those excluded by pairing.

Thus early versus all-paired isolates the cap. Full-pool search also removes the
pairing constraint; its difference must not all be attributed to four slots.

At every prediction, a donor must match the already emitted raw word prefix,
the completed modeled spelling, and preceding bits of the current modeled byte.
It must have remaining raw and modeled spelling. Selection receives no target
bit. Each matching donor emits the same rounded half-parent/half-copy binary
distribution; donors have uniform weight, and an empty set returns the parent.
All distributions are normalized and nonzero.

There are no persistent donor weights or outer mixtures in these new shadow arms.
The new early arm is consequently a selection control, not a replay of the old
I/S scientific treatment. Separately, the original S model is replayed to verify
the retained state and inverse. This diagnostic neither explains the old archive
loss completely nor substitutes for a later finite-codec comparison.

## Additional coverage and its cost

Positive values in the last column mean the expert costs more than the parent.
Each row compares identical prospectively selected bit events.

| Opportunity set | Events | Parent cost / perfect-prediction ceiling, bits | Expert used | Expert cost, bits | Expert loss, bits |
| --- | ---: | ---: | --- | ---: | ---: |
| Additional pair-eligible donors beyond four | 444 | 64.182211 | All paired | 84.118184 | 19.935973 |
| Additional donors excluded by pairing | 905 | 192.409656 | Full pool | 252.928427 | 60.518772 |
| Union of all additional donors | 1,178 | 210.390918 | Full pool | 281.792679 | 71.401761 |

The first two sets overlap on 171 events; their costs cannot be added. On the
union, the full-pool expert also loses 59.199018 bits against the early control.
The four-slot expansion alone loses 11.331566 bits against that control.

There are **379 additional donor discoveries**, counted once per donor occurrence
within a mention and epoch, not 379 globally distinct spellings. Their union's
optimistic ceiling is **26.298865 ideal bytes on this sample**; the cap-only
ceiling is 8.022776 ideal bytes. These are not finite-archive savings and must not
be multiplied into a full-corpus forecast. Wrong continuations and predictions
at actual word endings remain in the prospective event population.

Both chronological directions lose on the additional events:

| Direction | Events | Parent ceiling, bits | Full-pool expert loss, bits |
| --- | ---: | ---: | ---: |
| Decoded title history to body | 299 | 77.148001 | 42.716850 |
| Decoded body history to later link text | 879 | 133.242917 | 28.684911 |

Across the complete modeled population, the early, all-paired and full-pool
experts lose **20.324100**, **31.655666** and **79.523118** bits respectively to
the unchanged parent. No global average is being used to hide a measured gain
on the declared additional-event set: that matched conditional set also loses.

## WRT geometry and resource price

Of 24,860 completed title/body words of at least three letters, **23,124** arrive
in a single inverse emission and **1,736** span multiple emissions. This is an
ex-post geometry census, not a rule selecting profitable targets. The spelling
inside a completed dictionary-word emission is already known before its raw
prefix could be queried.

The [event ledger](../results/fx2_donor_coverage250k_q0_v1/work/replay.tsv) retains
each additional event's modeled coordinate, role, parent and all three expert
probabilities, candidate counts, truth, and remaining candidate suffix bounds.
Those suffix bounds range from **1 to 192 still-unknown modeled bits**. They
describe candidate continuations, not future-confirmed lengths of actual words.
Some continuations are wrong; the diagnostic charges their losses rather than
discarding them after observing the target.

The scan performs 11,854,920 donor examinations and 9,773,240 explicit byte
comparisons, plus 57,078,792 pairing-loop checks. Of 74,240 raw-prefix match
incidences, 71,116 fail modeled-coordinate compatibility. These are repeated
donor/event checks, not unique words. The diagnostic recomputes selection and
serializes reference state; it is not an optimized index benchmark.

At most 64 frozen records per role were retained; the largest serialized original
state inspected was 6,318 bytes. That number excludes duplicate frozen pools,
dictionary, allocator overhead, trace buffers and other process memory.
The [guard](../run_logs/adaptive/20260920T185146Z_aebb847936.resources/guard.json)
records a 224,030,720-byte cgroup peak including compilation and 5,545,984 peak
allocated scratch bytes. CPU 2 was assigned under a 1 GiB memory, 128 MiB scratch,
240-second job envelope. All guard flags are false and cleanup is complete.
Shared-host diagnostic timing supplies no prize qualification.

## Acceptance and stopping decision

- Four targeted pytest tests pass, including native undefined-behavior checks,
  prospective donor selection, complete-emission boundaries and the existing
  relational state/posterior fixtures.
- The explicit native CI group passes all 14 tests with this fixture included;
  [the check receipt](../operations/evidence/fx2_donor_coverage_20260920_tests.json)
  binds the commands and changed test sources.
- The 250,000-byte raw inverse and retained original introduced-state witnesses
  match exactly. Original accumulated costs agree within the declared 1e-6-bit
  floating-point tolerance; this is not a claim of bit-identical floating sums.
- Replaying twice produces identical measurements, event ledgers and state files.
- All 46 original output-manifest artifacts were rehashed. An independent Python
  summation checks all 1,178 ledger rows against retained trace probabilities and
  truths, recomputes the conditional costs, and confirms the overlapping sets.
- A canonical terminal index and one diagnostic run-ledger row are published.
  Archive bytes, package bytes, compression roundtrip and prize score remain null.

The frozen discriminator required at least 256 bits of prospective parent cost
and an all-pool distribution beating both parent and early control. Neither
condition passes. The 256-bit cutoff is an explicit planning threshold, not an
information-theoretic impossibility result.

**Stop this particular transfer before implementing another native predictor.**
Preserve both imports as implementation references and keep the broader relation
hypothesis open. A partial modeled-codeword signal, different representation or
other relationship would require a separately justified experiment; none is
selected here. The 96M target and 95M stretch are unchanged, and Gamma's verified
full-corpus score remains unknown.

Component intent is preserved: the new adapter owns analysis policy and uses
existing execution, closure and publication services. The source charter now
explicitly includes adapter-owned native diagnostics while preserving execution
and lifecycle authority. The coverage fixture is included in the explicit native
CI group. It changes no codec. Revalidation uses the existing entrance:

```bash
python3 tools/research_contracts.py operations/adaptive/reflections/20260920T185146Z_aebb847936.json
python3 tools/record_driver_result.py fx2_donor_coverage250k_q0_v1 --terminal-index results/fx2_donor_coverage250k_q0_v1/terminal-index.json --check
```
