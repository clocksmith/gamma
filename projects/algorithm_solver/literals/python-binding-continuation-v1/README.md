# Python scope naming continuation

[Freeze](FREEZE.md), [newline amendment](AMENDMENT-1.md), [review receipt](REVIEW.md), [design](DESIGN.md), [metadata evidence](evidence/results.json).

Selected development successor: **none**. Python only: 27 fit and nine consumed validation problems. No protected access, new confirmation, M1 qualification or JS/Python pooled claim.

| Entries | Arm | Split | Decode | Qualify | Selections | Median | p90 | p95 | Actions | Character fraction | Package |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | control | fit | 27/27 | 27/27 | 3680 | 126 | 231 | 258 | 3707 | 69.89% | 5142 |
| 128 | control | validation | 9/9 | 9/9 | 1411 | 127 | 252 | 252 | 1420 | 74.27% | 2411 |
| 128 | global | fit | 27/27 | 27/27 | 3680 | 126 | 231 | 258 | 3707 | 69.89% | 5142 |
| 128 | global | validation | 9/9 | 9/9 | 1411 | 127 | 252 | 252 | 1420 | 74.27% | 2411 |
| 128 | global_joint | fit | 27/27 | 27/27 | 3680 | 126 | 231 | 258 | 3707 | 69.89% | 5142 |
| 128 | global_joint | validation | 9/9 | 9/9 | 1411 | 127 | 252 | 252 | 1420 | 74.27% | 2411 |
| 128 | scope | fit | 27/27 | 27/27 | 3680 | 126 | 231 | 258 | 3707 | 69.89% | 5142 |
| 128 | scope | validation | 9/9 | 9/9 | 1411 | 127 | 252 | 252 | 1420 | 74.27% | 2411 |
| 128 | scope_joint | fit | 27/27 | 27/27 | 3680 | 126 | 231 | 258 | 3707 | 69.89% | 5142 |
| 128 | scope_joint | validation | 9/9 | 9/9 | 1411 | 127 | 252 | 252 | 1420 | 74.27% | 2411 |
| 256 | control | fit | 27/27 | 27/27 | 2006 | 66 | 145 | 153 | 2033 | 46.66% | 5524 |
| 256 | control | validation | 9/9 | 9/9 | 940 | 97 | 181 | 181 | 949 | 57.77% | 3720 |
| 256 | global | fit | 27/27 | 27/27 | 1993 | 66 | 144 | 150 | 2020 | 46.31% | 5511 |
| 256 | global | validation | 9/9 | 9/9 | 929 | 97 | 180 | 180 | 938 | 56.94% | 3709 |
| 256 | global_joint | fit | 27/27 | 27/27 | 1986 | 66 | 144 | 144 | 2013 | 46.63% | 5519 |
| 256 | global_joint | validation | 9/9 | 9/9 | 926 | 97 | 180 | 180 | 935 | 56.91% | 3721 |
| 256 | scope | fit | 27/27 | 27/27 | 1993 | 66 | 144 | 150 | 2020 | 46.31% | 5511 |
| 256 | scope | validation | 9/9 | 9/9 | 929 | 97 | 180 | 180 | 938 | 56.94% | 3709 |
| 256 | scope_joint | fit | 27/27 | 27/27 | 1986 | 66 | 144 | 144 | 2013 | 46.63% | 5519 |
| 256 | scope_joint | validation | 9/9 | 9/9 | 926 | 97 | 180 | 180 | 935 | 56.91% | 3721 |

Costs include encoded candidates; failed qualification invalidates gain claims. Exact packet decoding, full source, dictionary,41-byte headers,padding and one Finish are charged. Decoder-source-inclusive costs add 13,010 bytes for the pinned literals.py and pass2/working/bitpack.py; per-program standalone costs charge the whole dictionary and both decoder sources. Installed Python/stdlib footprint is unmeasured. All eligible locals are compared under the same conservative scope rules; public parameter names and captured names remain fixed.

| Entries | Arm | Better/same/worse vs baseline | Baseline ready | Searched-control ready | Scope successor | Failed predicates |
| ---: | --- | --- | --- | --- | --- | --- |
| 128 | control | 0/9/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:p90, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:p90, checks_control:improved |
| 128 | global | 0/9/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:p90, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:p90, checks_control:improved |
| 128 | global_joint | 0/9/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:p90, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:p90, checks_control:improved |
| 128 | scope | 0/9/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:p90, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:p90, checks_control:improved, checks_matched_global:actions |
| 128 | scope_joint | 0/9/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:p90, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:p90, checks_control:improved, checks_matched_global:actions |
| 256 | control | 0/9/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:p90, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:p90, checks_control:improved |
| 256 | global | 3/6/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:improved |
| 256 | global_joint | 3/6/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:improved |
| 256 | scope | 3/6/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:improved, checks_matched_global:actions |
| 256 | scope_joint | 3/6/0 | False | False | False | checks_baseline:actions, checks_baseline:median, checks_baseline:improved, checks_control:actions, checks_control:median, checks_control:improved, checks_matched_global:actions |

| Prediction | Met |
| --- | --- |
| P1 | True |
| P2 | False |
| P3 | False |
| P4 | True |
| P5 | True |

Fresh qualification: 8/8 distinct changed programs, 950/950 checks passed. Original sources reuse exact-hash passing item6 receipts. No retries or repairs.

Measured run wall time: 18.83 seconds. Search/qualification counts, stop reasons and per-ID metadata are in evidence. The 29 prelaunch synthetic checks establish focused implementation checks, not numerical qualification.

M1 remains400/500,<=256entries,median<=32,p95<=96selections,<=10%single-character bits,zero whole-solution entries. This36-program panel cannot qualify it. Component intent preserved; no production, admission or publication authority changed.

Rebuild with `python3 -B projects/algorithm_solver/literals/python-binding-continuation-v1/report.py --run /private/run/path`.
