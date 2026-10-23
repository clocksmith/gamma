# Scope-local naming and vocabulary-aware selection

[Freeze](FREEZE.md) pushed in `1e2271151`; [review/run receipt](REVIEW.md); [sanitized evidence](evidence/results.json). [Contract metadata clarification](NOTE-2026-10-23-CONTRACT-METADATA.md).

Input candidate: **none**. These are consumed-development source-plus-encoder results. They do not establish M1 qualification, independent generalization or autonomous assembly.

Scope-local naming adds little over the matched printer control in this fixed alphabet family: joint128 saves 21 validation actions (0.15%, 5 better/84 same/11 worse), while joint256 saves 28 (0.31%, 2/98/0). Neither arm passes readiness. Only three validation programs choose a mangled profile in each joint arm. Their total binding count is unchanged; distinct spellings decrease from 762 to 749. This measures the fixed family, not the best possible per-binding search.

## Costs and qualification

| Entries | Arm | Split | Source bytes | Decode / qualify | Changed | Selections | Median / p90 / p95 / worst | <=32 / <=96 | Actions | Single-char | Package bytes |
| ---: | --- | --- | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 128 | control | fit | 75474 | 300/300 of 300 | 105 | 41511 | 107.0/256/302/1172 | 9/128 | 41811 | 79.69% | 49574 |
| 128 | control | validation | 25726 | 100/100 of 100 | 42 | 13849 | 102.5/245/322/715 | 5/47 | 13949 | 79.10% | 17083 |
| 128 | default | fit | 75764 | 300/300 of 300 | 45 | 41577 | 107.0/255/303/1173 | 10/128 | 41877 | 79.55% | 49631 |
| 128 | default | validation | 25819 | 100/100 of 100 | 23 | 13944 | 103.5/260/320/716 | 5/45 | 14044 | 79.12% | 17163 |
| 128 | joint | fit | 75398 | 300/300 of 300 | 106 | 41462 | 107.0/256/302/1172 | 9/128 | 41762 | 79.64% | 49534 |
| 128 | joint | validation | 25680 | 100/100 of 100 | 42 | 13828 | 103.0/251/322/715 | 5/46 | 13928 | 79.04% | 17063 |
| 128 | select | fit | 75726 | 300/300 of 300 | 45 | 41528 | 107.0/255/303/1173 | 10/128 | 41828 | 79.52% | 49589 |
| 128 | select | validation | 25791 | 100/100 of 100 | 23 | 13916 | 103.5/260/320/716 | 5/45 | 14016 | 79.07% | 17138 |
| 256 | control | fit | 75961 | 300/300 of 300 | 8 | 26040 | 67.5/161/188/930 | 49/216 | 26340 | 54.17% | 40546 |
| 256 | control | validation | 25906 | 100/100 of 100 | 7 | 8936 | 63.5/169/210/501 | 13/70 | 9036 | 55.45% | 15242 |
| 256 | default | fit | 76100 | 300/300 of 300 | 3 | 26108 | 68.0/162/188/930 | 48/216 | 26408 | 54.09% | 40615 |
| 256 | default | validation | 25958 | 100/100 of 100 | 5 | 8948 | 63.5/169/211/501 | 13/69 | 9048 | 55.29% | 15255 |
| 256 | joint | fit | 75895 | 300/300 of 300 | 9 | 26001 | 67.5/161/188/930 | 49/216 | 26301 | 54.03% | 40507 |
| 256 | joint | validation | 25860 | 100/100 of 100 | 7 | 8908 | 63.5/169/210/501 | 13/70 | 9008 | 55.21% | 15214 |
| 256 | select | fit | 75974 | 300/300 of 300 | 7 | 26078 | 68.0/162/188/930 | 48/216 | 26378 | 54.10% | 40585 |
| 256 | select | validation | 25908 | 100/100 of 100 | 6 | 8923 | 63.5/169/211/501 | 13/69 | 9023 | 55.23% | 15230 |

Every final packet independently decodes to the selected source hash. Changed final sources undergo all original cases and strict observation parity; unchanged R sources reuse qualification. No retry, candidate repair or test-driven fallback. Any failure stays in the denominator and invalidates readiness. One Finish is included per program; framing, padding and dictionary bytes are charged.

Canonical decoder dependencies add 13,010 source-file bytes per package. Offline compiler/generator tooling is 2,563,338 bytes, reported separately from decoder/input storage. Installed Node/CPython/stdlib footprints remain unmeasured. Per-program and amortized storage, framing/padding and action distributions are in the evidence.

## Paired validation and readiness

| Entries | Arm | Better / same / worse vs searched control | vs pinned R | Ready | Failed predicates |
| ---: | --- | --- | --- | --- | --- |
| 128 | control | 0/100/0 | 53/24/23 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 128 | default | 23/24/53 | 5/95/0 | False | actions_5_percent, median_lower, p90_lower, improved_60, worsened_at_most_25, fallback_nonincrease |
| 128 | joint | 5/84/11 | 52/25/23 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 128 | select | 26/24/50 | 5/95/0 | False | actions_5_percent, median_lower, p90_lower, improved_60, worsened_at_most_25 |
| 256 | control | 0/100/0 | 19/79/2 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 256 | default | 2/79/19 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 256 | joint | 2/98/0 | 21/78/1 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 256 | select | 3/78/19 | 2/98/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |

Default/select uses the same fixed dictionary and printer; the difference is the additional fixed alphabet family. Joint/select adds dictionary adaptation; joint/control compares naming plus dictionary optimization against continued original-plus-printer search. Validation sources are optimized under already sealed dictionaries.

## Source choices and search

| Entries | Arm | Validation profile counts | Skips / failed variants | Trials | Stop | Search seconds |
| ---: | --- | --- | --- | ---: | --- | ---: |
| 128 | control | {"layout": 42, "original": 58} | 0/0 | 2335 | local_optimum | 37.51 |
| 128 | default | {"default": 1, "layout": 22, "original": 77} | 0/0 | 1 | fixed_dictionary | 0.03 |
| 128 | joint | {"layout": 39, "original": 58, "rotate00": 3} | 0/0 | 2335 | local_optimum | 168.83 |
| 128 | select | {"layout": 20, "original": 77, "rotate00": 3} | 0/0 | 1 | fixed_dictionary | 0.13 |
| 256 | control | {"layout": 7, "original": 93} | 0/0 | 1813 | local_optimum | 18.95 |
| 256 | default | {"layout": 5, "original": 95} | 0/0 | 1 | fixed_dictionary | 0.04 |
| 256 | joint | {"layout": 4, "original": 93, "rotate00": 3} | 0/0 | 1813 | local_optimum | 68.26 |
| 256 | select | {"layout": 4, "original": 94, "rotate00": 2} | 0/0 | 1 | fixed_dictionary | 0.15 |

## Binding-name reuse and historical comparison

| Entries | Arm | Validation diagnostics | Bindings | Distinct spellings summed per program |
| ---: | --- | ---: | ---: | ---: |
| 128 | control | 100/100 | 904 | 762 |
| 128 | default | 100/100 | 904 | 757 |
| 128 | joint | 100/100 | 904 | 749 |
| 128 | select | 100/100 | 904 | 749 |
| 256 | control | 100/100 | 904 | 762 |
| 256 | default | 100/100 | 904 | 762 |
| 256 | joint | 100/100 | 904 | 749 |
| 256 | select | 100/100 | 904 | 755 |

Binding-name reuse is a diagnostic, not a proof of semantic equivalence. Missing scope-analysis diagnostics remain explicitly unavailable.
Historical name-search joint128 used 14006 validation actions and 17133 raw package bytes. That experiment used a global injective spelling map and a different search; this is a historical contrast, not a matched arm.
Historical name-search joint256 used 8684 validation actions and 14908 raw package bytes. That experiment used a global injective spelling map and a different search; this is a historical contrast, not a matched arm.

Compiler skips retain the unchanged original and full denominator. Compiler failures remove only that generated alternative before selection; final qualification failures never trigger replacement. Local or budget-limited termination is not a global optimum.

| Prediction | Met |
| --- | --- |
| S1 | False |
| S2 | False |
| S3 | False |
| S4 | True |
| S5 | True |
| S6 | True |

S2’s no-worsening clause is a consistency check by construction: select minimizes the same fixed-dictionary cost over a superset containing the default-mangler choices. Its requirement of at least 20 strict improvements per width is empirical.

Independent execution: 163/163 distinct changed programs, 15,632/15,632 checks. Measured total run wall time: 192.21 seconds. Nine scope checks, three choice checks and compilation/import passed before launch. The unchanged judge/lane infrastructure retains A’s 37 checks.

Source bodies, dictionaries, variants, sequences, errors and cases remain private. A ready input candidate only motivates a separately frozen owner-approved confirmation. No held-out opening, training, source publication, BITS deployment, human study or M1 threshold change. Component intent preserved; canonical decoder and production interfaces unchanged.

Rebuild: `python3 -B projects/algorithm_solver/literals/scope-choice-v1/report.py --run /private/path/to/scope-choice/run-v1`.
