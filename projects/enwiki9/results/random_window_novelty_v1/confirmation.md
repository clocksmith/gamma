# Random-Window Novelty Screen

- Phase: `confirmation`
- Corpus bytes: `1000000000`
- Corpus SHA-256: `159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`
- Window sizes: `500000, 1000000`
- Windows per size: `8`
- Evidence: `level_1_proxy_reversible_transform`
- Claim boundary: proxy gains do not change the enwik9 score forecast or prove 10.95%.
- Promotion boundary: a qualifying row earns an exact FX2 residual/component trace with counted code; it does not earn a native gate.

## Ranked Decisions

| Algorithm | Role | Family | Minimum gain B/1M | Mean gain B/1M | Decision |
|---|---|---|---:|---:|---|
| `title_echo` | `candidate` | `title_echo` | 1614.000 | 1963.500 | `exact_fx2_trace_earned` |
| `title_echo_previous_control` | `matched_control` | `title_echo_control` | -269.750 | -252.250 | `control_only` |

## Scope Summaries

| Algorithm | Backend | Scope | Windows | Delta bytes | Gain B/1M | W/T/R | Worst regression |
|---|---|---:|---:|---:|---:|---:|---:|
| `title_echo` | `bz2_9` | 500,000 | 8 | -7185 | 1796.250 | 8/0/0 | -448 |
| `title_echo` | `bz2_9` | 1,000,000 | 8 | -22162 | 2770.250 | 8/0/0 | -1911 |
| `title_echo` | `lzma_6` | 500,000 | 8 | -6456 | 1614.000 | 8/0/0 | -512 |
| `title_echo` | `lzma_6` | 1,000,000 | 8 | -13388 | 1673.500 | 8/0/0 | -1108 |
| `title_echo_previous_control` | `bz2_9` | 500,000 | 8 | +1079 | -269.750 | 1/0/7 | +397 |
| `title_echo_previous_control` | `bz2_9` | 1,000,000 | 8 | +1690 | -211.250 | 2/0/6 | +794 |
| `title_echo_previous_control` | `lzma_6` | 500,000 | 8 | +1056 | -264.000 | 1/0/7 | +528 |
| `title_echo_previous_control` | `lzma_6` | 1,000,000 | 8 | +2112 | -264.000 | 0/0/8 | +1032 |

## Interpretation

Negative archive deltas and positive gain rates are improvements over raw input under the same backend. The algorithm source/package cost is not counted in this proxy receipt. Backend disagreement, window regressions, or failure to clear 700 gross bytes per million at every tested scope prevents promotion.
