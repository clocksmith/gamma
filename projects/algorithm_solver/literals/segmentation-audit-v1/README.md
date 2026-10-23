# Fixed-source segmentation and character-tail audit

[Freeze](FREEZE.md) pushed as `c036ba20c`; [review/run receipt](REVIEW.md), [sanitized evidence](evidence/results.json). Source, dictionary and sequence artifacts remain private.

This measures exact alternative segmentations of already qualified programs. Historical canonical packets and encoders remain unchanged. Seeds and their selection use consumed development evidence; this is neither independent confirmation nor a new source/dictionary readiness result.

At control256, minimizing character codes among shortest paths changes validation codes from 4934 to 4855 (1.60% fewer), with 9048 actions unchanged. Minimizing absolute character codes first yields 4850 codes at 9060 actions.

| Seed | Policy | Split | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Character codes | Character fraction | Package bytes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| control128 | canonical | fit | 41684 | 107.0 | 256 | 303 | 1173 | 10/128 | 41984 | 33021 | 79.22% | 49725 |
| control128 | canonical | validation | 14014 | 103.5 | 267 | 320 | 716 | 5/45 | 14114 | 11025 | 78.67% | 17225 |
| control128 | shortest_min_char | fit | 41684 | 107.0 | 256 | 303 | 1173 | 10/128 | 41984 | 33021 | 79.22% | 49725 |
| control128 | shortest_min_char | validation | 14014 | 103.5 | 267 | 320 | 716 | 5/45 | 14114 | 11025 | 78.67% | 17225 |
| control128 | shortest_max_char | fit | 41684 | 107.0 | 256 | 303 | 1173 | 10/128 | 41984 | 33021 | 79.22% | 49725 |
| control128 | shortest_max_char | validation | 14014 | 103.5 | 267 | 320 | 716 | 5/45 | 14114 | 11025 | 78.67% | 17225 |
| control128 | min_char | fit | 41684 | 107.0 | 256 | 303 | 1173 | 10/128 | 41984 | 33021 | 79.22% | 49725 |
| control128 | min_char | validation | 14014 | 103.5 | 267 | 320 | 716 | 5/45 | 14114 | 11025 | 78.67% | 17225 |
| control256 | canonical | fit | 26108 | 68.0 | 162 | 188 | 930 | 48/216 | 26408 | 14115 | 54.06% | 40615 |
| control256 | canonical | validation | 8948 | 63.5 | 169 | 211 | 501 | 13/69 | 9048 | 4934 | 55.14% | 15255 |
| control256 | shortest_min_char | fit | 26108 | 68.0 | 162 | 188 | 930 | 48/216 | 26408 | 13891 | 53.21% | 40615 |
| control256 | shortest_min_char | validation | 8948 | 63.5 | 169 | 211 | 501 | 13/69 | 9048 | 4855 | 54.26% | 15255 |
| control256 | shortest_max_char | fit | 26108 | 68.0 | 162 | 188 | 930 | 48/216 | 26408 | 14125 | 54.10% | 40615 |
| control256 | shortest_max_char | validation | 8948 | 63.5 | 169 | 211 | 501 | 13/69 | 9048 | 4942 | 55.23% | 15255 |
| control256 | min_char | fit | 26137 | 68.0 | 162 | 188 | 930 | 48/216 | 26437 | 13871 | 53.07% | 40644 |
| control256 | min_char | validation | 8960 | 63.5 | 169 | 211 | 501 | 13/69 | 9060 | 4850 | 54.13% | 15267 |
| scope256 | canonical | fit | 24915 | 64.5 | 151 | 177 | 893 | 49/221 | 25215 | 12458 | 50.00% | 39422 |
| scope256 | canonical | validation | 8476 | 62.5 | 156 | 197 | 477 | 16/70 | 8576 | 4290 | 50.61% | 14783 |
| scope256 | shortest_min_char | fit | 24915 | 64.5 | 151 | 177 | 893 | 49/221 | 25215 | 12240 | 49.13% | 39422 |
| scope256 | shortest_min_char | validation | 8476 | 62.5 | 156 | 197 | 477 | 16/70 | 8576 | 4217 | 49.75% | 14783 |
| scope256 | shortest_max_char | fit | 24915 | 64.5 | 151 | 177 | 893 | 49/221 | 25215 | 12467 | 50.04% | 39422 |
| scope256 | shortest_max_char | validation | 8476 | 62.5 | 156 | 197 | 477 | 16/70 | 8576 | 4298 | 50.71% | 14783 |
| scope256 | min_char | fit | 24941 | 65.0 | 151 | 177 | 893 | 49/221 | 25241 | 12223 | 49.01% | 39448 |
| scope256 | min_char | validation | 8484 | 62.5 | 156 | 197 | 477 | 16/70 | 8584 | 4214 | 49.67% | 14791 |
| scope_joint256 | canonical | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12328 | 49.81% | 39270 |
| scope_joint256 | canonical | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4193 | 49.89% | 14724 |
| scope_joint256 | shortest_min_char | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12139 | 49.05% | 39270 |
| scope_joint256 | shortest_min_char | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4129 | 49.13% | 14724 |
| scope_joint256 | shortest_max_char | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12341 | 49.86% | 39270 |
| scope_joint256 | shortest_max_char | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4202 | 50.00% | 14724 |
| scope_joint256 | min_char | fit | 24776 | 64.5 | 150 | 176 | 886 | 52/222 | 25076 | 12122 | 48.93% | 39296 |
| scope_joint256 | min_char | validation | 8412 | 61.5 | 154 | 199 | 477 | 17/70 | 8512 | 4126 | 49.05% | 14732 |

Each row covers and reuses qualification for all300 fit or100 validation programs. One Finish per program; unchanged7/8-bit width, dictionary bytes,41-byte framing and padding all charged. Decoder-inclusive packages and offline additional encoder bytes are in evidence; full runtime installation storage remains unmeasured.

| Seed | Policy | Validation character count better/same/worse | Validation selections better/same/worse |
| --- | --- | --- | --- |
| control128 | canonical | 0/100/0 | 0/100/0 |
| control128 | shortest_min_char | 0/100/0 | 0/100/0 |
| control128 | shortest_max_char | 0/100/0 | 0/100/0 |
| control128 | min_char | 0/100/0 | 0/100/0 |
| control256 | canonical | 0/100/0 | 0/100/0 |
| control256 | shortest_min_char | 49/51/0 | 0/100/0 |
| control256 | shortest_max_char | 0/92/8 | 0/100/0 |
| control256 | min_char | 51/49/0 | 0/95/5 |
| scope256 | canonical | 0/100/0 | 0/100/0 |
| scope256 | shortest_min_char | 47/53/0 | 0/100/0 |
| scope256 | shortest_max_char | 0/94/6 | 0/100/0 |
| scope256 | min_char | 49/51/0 | 0/97/3 |
| scope_joint256 | canonical | 0/100/0 | 0/100/0 |
| scope_joint256 | shortest_min_char | 45/55/0 | 0/100/0 |
| scope_joint256 | shortest_max_char | 0/93/7 | 0/100/0 |
| scope_joint256 | min_char | 47/53/0 | 0/97/3 |

`shortest_min_char` and `shortest_max_char` give the exact character-count range among minimum-selection paths for these fixed sources/dictionaries. At that fixed count, character fraction has the same ordering. `min_char` minimizes absolute character codes, then selections; it does not minimize fraction and cannot bound fraction when a larger denominator is allowed. These are restricted encoding optima, not dictionary-search or representation impossibility results.

| Prediction | Met |
| --- | --- |
| T1 | True |
| T2 | False |
| T3 | False |
| T4 | True |

All 6,400 packets independently decode and are rechecked during reporting; canonical sequences exactly reproduce the existing encoder and published N/C counts. Every per-program objective inequality passed. Source qualification and whole-source/body legality are reused from item13 with unchanged hashes, not freshly executed cases. Measured wall time: 2.38 seconds. Four focused tests include150 exhaustive tiny examples under all four policies.

No new candidate promotion is requested by this audit. Changing the canonical encoder or promoting an alternative needs a separate freeze and review; owner-approved independent confirmation remains required for broader claims. Final held-out/protected sets stay closed. No source rewrite, training, deployment, publication, human study, ledger/catalog/claim write or M1 threshold change. Component intent and production boundaries preserved.

Rebuild: `python3 -B projects/algorithm_solver/literals/segmentation-audit-v1/report.py --run /private/segmentation-audit/run-v1 --work /private/literal-admission500-v1`.
