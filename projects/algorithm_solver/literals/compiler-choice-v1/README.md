# Compiler alternatives and vocabulary-aware selection

[Freeze](FREEZE.md) pushed in `fe0cb9290`; [review/run receipt](REVIEW.md); [sanitized evidence](evidence/results.json).

Input candidate: **none**. These are consumed-development source-plus-encoder results. They do not establish M1 qualification, independent generalization or autonomous assembly.

The 128-entry joint arm saves 745 of 14,114 validation actions (5.28%), improves 81 programs and worsens 11, and reduces raw package bytes from 17,225 to 16,577. Its only failed readiness predicate is single-character fraction, which rises from 78.67% to 81.95%. At 256 entries joint saves only 14 actions (0.15%). Byte-minimum sources are 9.45% shorter on validation but cost more inputs under the initial dictionaries: 2.88% more at 128 and 13.19% more at 256. Source-byte minimization and literal-input minimization differ.

## Costs and qualification

| Entries | Arm | Split | Source bytes | Decode / qualify | Changed | Selections | Median / p90 / p95 / worst | <=32 / <=96 | Actions | Single-char | Package bytes |
| ---: | --- | --- | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 128 | bytes | fit | 69068 | 300/300 of 300 | 295 | 43013 | 114.0/260/310/1234 | 5/119 | 43313 | 87.80% | 50884 |
| 128 | bytes | validation | 23535 | 100/100 of 100 | 100 | 14420 | 109.5/259/314/725 | 4/38 | 14520 | 87.48% | 17581 |
| 128 | control | fit | 76107 | 300/300 of 300 | 0 | 41684 | 107.0/256/303/1173 | 10/128 | 41984 | 79.22% | 49725 |
| 128 | control | validation | 25992 | 100/100 of 100 | 0 | 14014 | 103.5/267/320/716 | 5/45 | 14114 | 78.67% | 17225 |
| 128 | joint | fit | 69195 | 300/300 of 300 | 294 | 39711 | 101.0/247/291/1146 | 17/136 | 40011 | 82.23% | 48009 |
| 128 | joint | validation | 23564 | 100/100 of 100 | 100 | 13269 | 102.0/235/304/679 | 7/47 | 13369 | 81.95% | 16577 |
| 128 | select | fit | 73145 | 300/300 of 300 | 114 | 41146 | 106.0/253/303/1166 | 10/131 | 41446 | 81.92% | 49254 |
| 128 | select | validation | 24880 | 100/100 of 100 | 46 | 13786 | 103.5/249/309/716 | 5/46 | 13886 | 81.56% | 17025 |
| 256 | bytes | fit | 69068 | 300/300 of 300 | 295 | 29836 | 77.0/178/212/1044 | 29/192 | 30136 | 65.23% | 44343 |
| 256 | bytes | validation | 23535 | 100/100 of 100 | 100 | 10141 | 76.0/181/251/526 | 8/63 | 10241 | 66.18% | 16448 |
| 256 | control | fit | 76107 | 300/300 of 300 | 0 | 26108 | 68.0/162/188/930 | 48/216 | 26408 | 54.06% | 40615 |
| 256 | control | validation | 25992 | 100/100 of 100 | 0 | 8948 | 63.5/169/211/501 | 13/69 | 9048 | 55.14% | 15255 |
| 256 | joint | fit | 75747 | 300/300 of 300 | 16 | 26029 | 67.5/161/188/930 | 49/216 | 26329 | 54.34% | 40535 |
| 256 | joint | validation | 25853 | 100/100 of 100 | 8 | 8934 | 63.5/169/210/501 | 13/70 | 9034 | 55.60% | 15240 |
| 256 | select | fit | 75881 | 300/300 of 300 | 12 | 26101 | 68.0/162/188/930 | 48/216 | 26401 | 54.28% | 40608 |
| 256 | select | validation | 25925 | 100/100 of 100 | 6 | 8948 | 63.5/169/211/501 | 13/69 | 9048 | 55.38% | 15255 |

Every final packet independently decodes to the selected source hash. Changed final sources undergo all original cases and strict observation parity; unchanged R sources reuse qualification. No retry, candidate repair or test-driven fallback. Any failure stays in the denominator and invalidates readiness. One Finish is included per program; framing, padding and dictionary bytes are charged.

Canonical decoder dependencies add 13,010 source-file bytes per package. Offline compiler/generator tooling is 2,460,549 bytes, reported separately from decoder/input storage. Installed Node/CPython/stdlib footprints remain unmeasured. Per-program and amortized storage, framing/padding and action distributions are in the evidence.

## Paired validation and readiness

| Entries | Arm | Better / same / worse vs searched control | vs pinned R | Ready | Failed predicates |
| ---: | --- | --- | --- | --- | --- |
| 128 | bytes | 23/4/73 | 23/4/73 | False | actions_5_percent, median_lower, improved_60, worsened_at_most_25, fallback_nonincrease |
| 128 | control | 0/100/0 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 128 | joint | 81/8/11 | 81/8/11 | False | fallback_nonincrease |
| 128 | select | 32/68/0 | 32/68/0 | False | actions_5_percent, median_lower, improved_60, fallback_nonincrease |
| 256 | bytes | 0/3/97 | 0/3/97 | False | actions_5_percent, median_lower, p90_lower, improved_60, worsened_at_most_25, fallback_nonincrease, package_within_105_percent |
| 256 | control | 0/100/0 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 256 | joint | 19/79/2 | 19/79/2 | False | actions_5_percent, median_lower, p90_lower, improved_60, fallback_nonincrease |
| 256 | select | 0/100/0 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60, fallback_nonincrease |

The bytes/select contrast uses the same fixed initial dictionary. Joint/select adds dictionary adaptation; joint/control compares complete source-plus-dictionary optimization against continued original-source search. Validation sources are optimized under already sealed dictionaries.

## Source choices and search

| Entries | Arm | Validation profile counts | Skips / failed variants | Trials | Stop | Search seconds |
| ---: | --- | --- | --- | ---: | --- | ---: |
| 128 | bytes | {"layout": 3, "standard": 97} | 0/0 | 1 | fixed_dictionary | 0.01 |
| 128 | control | {"original": 100} | 0/0 | 779 | local_optimum | 6.77 |
| 128 | joint | {"layout": 3, "standard": 52, "syntax": 45} | 0/0 | 8559 | local_optimum | 252.26 |
| 128 | select | {"layout": 10, "original": 54, "standard": 19, "syntax": 17} | 0/0 | 1 | fixed_dictionary | 0.04 |
| 256 | bytes | {"layout": 3, "standard": 97} | 0/0 | 1 | fixed_dictionary | 0.01 |
| 256 | control | {"original": 100} | 0/0 | 907 | local_optimum | 5.76 |
| 256 | joint | {"layout": 6, "original": 92, "standard": 1, "syntax": 1} | 0/0 | 1813 | local_optimum | 31.56 |
| 256 | select | {"layout": 5, "original": 94, "standard": 1} | 0/0 | 1 | fixed_dictionary | 0.05 |

Compiler skips retain the unchanged original and full denominator. Compiler failures remove only that generated alternative before selection; final qualification failures never trigger replacement. Local or budget-limited termination is not a global optimum.

| Prediction | Met |
| --- | --- |
| C1 | True |
| C2 | False |
| C3 | True |
| C4 | False |
| C5 | True |
| C6 | True |

C3’s no-worsening clause is a consistency check by construction: select minimizes the same fixed-dictionary cost over a superset containing the byte-minimum choice. Its requirement of at least 20 strict improvements per width is empirical.

Independent execution: 589/589 distinct changed programs, 57,280/57,280 checks. Measured total run wall time: 326.61 seconds. Seven compiler checks, three choice checks and compilation/import passed before launch. The unchanged judge/lane infrastructure retains A’s 37 checks.

Source bodies, dictionaries, variants, sequences, errors and cases remain private. A ready input candidate only motivates a separately frozen owner-approved confirmation. No held-out opening, training, source publication, BITS deployment, human study or M1 threshold change. Component intent preserved; canonical decoder and production interfaces unchanged.

Rebuild: `python3 -B projects/algorithm_solver/literals/compiler-choice-v1/report.py --run /private/path/to/compiler-choice/run-v1`.
