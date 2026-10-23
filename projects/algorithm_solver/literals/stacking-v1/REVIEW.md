# Review and execution receipt

Freeze 3ec1f7392 and prelaunch cap amendment c2925194b were pushed before
execution. Claude approved the design and the 7,200-second guard at 22:12Z on
2026-10-23. Items 22/29 were unrecorded at freeze time; item 27 was null.
Item 14's seven-action gain is included without treating it as a ready successor.

Launched at 22:12Z on cores 0–7. The supervisor exited zero after 835.08 seconds
(834.77 measured execution), without timeout. All 8,800 packets decode. All
65 distinct newly selected sources pass 6,026/6,026 checks; unchanged sources
reuse exact item13-R/item15-seed receipts. No failures were retried or replaced.
All fit outputs sealed before validation, and all choices before qualification.

Independent reporting initially stopped at a reference JSON serialization
assertion. The [dated reporting correction](NOTE-2026-10-23-reporting.md) retains
the original file-hash check and compares exact source-map/vocabulary values
after parsing. It changes no execution hash, input, cost or acceptance rule.
Thirteen focused reporter tests pass, including actual-source corruption
rejection. Full replay then passed: all packets/IDs/costs, source and dictionary
identities, retained-variant bans, fit/validation seals and qualification receipts.

No new successor under either encoder policy. D10 has the lowest total:
8,324 validation actions versus item24's 8,336, with median 61.5 selections,
p95 174 versus 197, and 22 better/64 same/14 worse. Under matched minN/minC,
its character share is 49.2096%, above item13's 49.1314% and item24's 48.8708%;
this fails the frozen incremental gate. Canonical comparisons fail the same
fraction condition. Its raw package is 15,014 bytes versus item24's 14,998.

D11 reduces minN/minC characters to 3,982 (48.3194%) but uses 8,341 actions,
median 62 selections and 27 worse programs versus item24. Weighted finishing
does not buy the character reduction without action/median costs. N/NC/NP/NCP
use 8,504/8,497/8,465/8,458 actions, exposing the small source-component gains.
Predictions S1–S4 pass, S5/S6 fail. Item24 remains the canonical selected default.

D11 nevertheless has full coverage, exact decoding and passing qualification,
so it is eligible for the separately frozen, predetermined structured2c study.
That does not select D11 as a flat successor. Component intent preserved; no
M1, protected opening, production change, training or independent confirmation.
