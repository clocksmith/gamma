# Random-Window Novelty Screen

- Phase: `selection`
- Corpus bytes: `1000000000`
- Corpus SHA-256: `159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`
- Window sizes: `500000, 1000000`
- Windows per size: `4`
- Evidence: `level_1_proxy_reversible_transform`
- Claim boundary: proxy gains do not change the enwik9 score forecast or prove 10.95%.
- Promotion boundary: a qualifying row earns an exact FX2 residual/component trace with counted code; it does not earn a native gate.

## Ranked Decisions

| Algorithm | Role | Family | Minimum gain B/1M | Mean gain B/1M | Decision |
|---|---|---|---:|---:|---|
| `title_echo` | `candidate` | `title_echo` | 1588.000 | 1908.438 | `confirmation_earned` |
| `title_echo_aliases` | `candidate` | `title_echo` | 1504.500 | 2108.000 | `confirmation_earned` |
| `title_echo_aliases_selective` | `candidate` | `title_echo` | 1326.500 | 1734.188 | `confirmation_earned` |
| `title_echo_selective` | `candidate` | `title_echo` | 1190.500 | 1549.188 | `confirmation_earned` |
| `title_echo_multiword` | `candidate` | `title_echo` | 926.000 | 1142.500 | `confirmation_earned` |
| `xml_id_delta` | `candidate` | `xml_id_delta` | -595.500 | -254.500 | `proxy_only_or_retire` |
| `title_echo_previous_control` | `matched_control` | `title_echo_control` | -649.500 | -336.250 | `control_only` |
| `wiki_graph_mtf64` | `candidate` | `wiki_graph_mtf` | -1672.000 | -700.562 | `proxy_only_or_retire` |
| `wiki_graph_mtf256` | `candidate` | `wiki_graph_mtf` | -2054.000 | -1033.938 | `proxy_only_or_retire` |
| `wiki_graph_mtf1024` | `candidate` | `wiki_graph_mtf` | -2448.000 | -1418.625 | `proxy_only_or_retire` |
| `rolling_phrase128k` | `candidate` | `rolling_phrase` | -4480.500 | -2670.250 | `proxy_only_or_retire` |
| `rolling_phrase64k` | `candidate` | `rolling_phrase` | -6670.500 | -4059.938 | `proxy_only_or_retire` |
| `rolling_phrase32k` | `candidate` | `rolling_phrase` | -9856.500 | -5866.375 | `proxy_only_or_retire` |
| `casefold_mask` | `candidate` | `casefold` | -29084.750 | -22725.688 | `proxy_only_or_retire` |
| `casefold_positions` | `candidate` | `casefold` | -29984.750 | -22717.688 | `proxy_only_or_retire` |

## Scope Summaries

| Algorithm | Backend | Scope | Windows | Delta bytes | Gain B/1M | W/T/R | Worst regression |
|---|---|---:|---:|---:|---:|---:|---:|
| `casefold_mask` | `bz2_9` | 500,000 | 4 | +47912 | -23956.000 | 0/0/4 | +14867 |
| `casefold_mask` | `bz2_9` | 1,000,000 | 4 | +116339 | -29084.750 | 0/0/4 | +30967 |
| `casefold_mask` | `lzma_6` | 500,000 | 4 | +36556 | -18278.000 | 0/0/4 | +11240 |
| `casefold_mask` | `lzma_6` | 1,000,000 | 4 | +78336 | -19584.000 | 0/0/4 | +20328 |
| `casefold_positions` | `bz2_9` | 500,000 | 4 | +50420 | -25210.000 | 0/0/4 | +16185 |
| `casefold_positions` | `bz2_9` | 1,000,000 | 4 | +119939 | -29984.750 | 0/0/4 | +32164 |
| `casefold_positions` | `lzma_6` | 500,000 | 4 | +33488 | -16744.000 | 0/0/4 | +10972 |
| `casefold_positions` | `lzma_6` | 1,000,000 | 4 | +75728 | -18932.000 | 0/0/4 | +20220 |
| `rolling_phrase128k` | `bz2_9` | 500,000 | 4 | +8961 | -4480.500 | 0/0/4 | +2576 |
| `rolling_phrase128k` | `bz2_9` | 1,000,000 | 4 | +13990 | -3497.500 | 0/0/4 | +4220 |
| `rolling_phrase128k` | `lzma_6` | 500,000 | 4 | +1448 | -724.000 | 1/0/3 | +788 |
| `rolling_phrase128k` | `lzma_6` | 1,000,000 | 4 | +7916 | -1979.000 | 0/0/4 | +2360 |
| `rolling_phrase32k` | `bz2_9` | 500,000 | 4 | +19713 | -9856.500 | 0/0/4 | +6637 |
| `rolling_phrase32k` | `bz2_9` | 1,000,000 | 4 | +24680 | -6170.000 | 0/0/4 | +7147 |
| `rolling_phrase32k` | `lzma_6` | 500,000 | 4 | +7320 | -3660.000 | 0/0/4 | +2240 |
| `rolling_phrase32k` | `lzma_6` | 1,000,000 | 4 | +15116 | -3779.000 | 0/0/4 | +4360 |
| `rolling_phrase64k` | `bz2_9` | 500,000 | 4 | +13341 | -6670.500 | 0/0/4 | +4149 |
| `rolling_phrase64k` | `bz2_9` | 1,000,000 | 4 | +20145 | -5036.250 | 0/0/4 | +5591 |
| `rolling_phrase64k` | `lzma_6` | 500,000 | 4 | +3572 | -1786.000 | 0/0/4 | +1396 |
| `rolling_phrase64k` | `lzma_6` | 1,000,000 | 4 | +10988 | -2747.000 | 0/0/4 | +3348 |
| `title_echo` | `bz2_9` | 500,000 | 4 | -3215 | 1607.500 | 4/0/0 | -196 |
| `title_echo` | `bz2_9` | 1,000,000 | 4 | -11385 | 2846.250 | 4/0/0 | -2563 |
| `title_echo` | `lzma_6` | 500,000 | 4 | -3176 | 1588.000 | 4/0/0 | -384 |
| `title_echo` | `lzma_6` | 1,000,000 | 4 | -6368 | 1592.000 | 4/0/0 | -1120 |
| `title_echo_aliases` | `bz2_9` | 500,000 | 4 | -3009 | 1504.500 | 3/0/1 | +268 |
| `title_echo_aliases` | `bz2_9` | 1,000,000 | 4 | -13574 | 3393.500 | 4/0/0 | -3110 |
| `title_echo_aliases` | `lzma_6` | 500,000 | 4 | -3284 | 1642.000 | 4/0/0 | -316 |
| `title_echo_aliases` | `lzma_6` | 1,000,000 | 4 | -7568 | 1892.000 | 4/0/0 | -1500 |
| `title_echo_aliases_selective` | `bz2_9` | 500,000 | 4 | -2653 | 1326.500 | 3/0/1 | +339 |
| `title_echo_aliases_selective` | `bz2_9` | 1,000,000 | 4 | -10697 | 2674.250 | 4/0/0 | -2252 |
| `title_echo_aliases_selective` | `lzma_6` | 500,000 | 4 | -2868 | 1434.000 | 4/0/0 | -168 |
| `title_echo_aliases_selective` | `lzma_6` | 1,000,000 | 4 | -6008 | 1502.000 | 4/0/0 | -1072 |
| `title_echo_multiword` | `bz2_9` | 500,000 | 4 | -1914 | 957.000 | 4/0/0 | -182 |
| `title_echo_multiword` | `bz2_9` | 1,000,000 | 4 | -6576 | 1644.000 | 4/0/0 | -1506 |
| `title_echo_multiword` | `lzma_6` | 500,000 | 4 | -1852 | 926.000 | 4/0/0 | -356 |
| `title_echo_multiword` | `lzma_6` | 1,000,000 | 4 | -4172 | 1043.000 | 4/0/0 | -740 |
| `title_echo_previous_control` | `bz2_9` | 500,000 | 4 | +1299 | -649.500 | 0/0/4 | +556 |
| `title_echo_previous_control` | `bz2_9` | 1,000,000 | 4 | +514 | -128.500 | 1/0/3 | +314 |
| `title_echo_previous_control` | `lzma_6` | 500,000 | 4 | +852 | -426.000 | 0/0/4 | +536 |
| `title_echo_previous_control` | `lzma_6` | 1,000,000 | 4 | +564 | -141.000 | 0/0/4 | +212 |
| `title_echo_selective` | `bz2_9` | 500,000 | 4 | -2381 | 1190.500 | 3/0/1 | +15 |
| `title_echo_selective` | `bz2_9` | 1,000,000 | 4 | -9341 | 2335.250 | 4/0/0 | -1976 |
| `title_echo_selective` | `lzma_6` | 500,000 | 4 | -2728 | 1364.000 | 4/0/0 | -332 |
| `title_echo_selective` | `lzma_6` | 1,000,000 | 4 | -5228 | 1307.000 | 4/0/0 | -868 |
| `wiki_graph_mtf1024` | `bz2_9` | 500,000 | 4 | +3685 | -1842.500 | 0/0/4 | +2539 |
| `wiki_graph_mtf1024` | `bz2_9` | 1,000,000 | 4 | -1092 | 273.000 | 3/0/1 | +113 |
| `wiki_graph_mtf1024` | `lzma_6` | 500,000 | 4 | +4896 | -2448.000 | 0/0/4 | +2116 |
| `wiki_graph_mtf1024` | `lzma_6` | 1,000,000 | 4 | +6628 | -1657.000 | 0/0/4 | +1924 |
| `wiki_graph_mtf256` | `bz2_9` | 500,000 | 4 | +2816 | -1408.000 | 1/0/3 | +2287 |
| `wiki_graph_mtf256` | `bz2_9` | 1,000,000 | 4 | -2069 | 517.250 | 4/0/0 | -200 |
| `wiki_graph_mtf256` | `lzma_6` | 500,000 | 4 | +4108 | -2054.000 | 0/0/4 | +2092 |
| `wiki_graph_mtf256` | `lzma_6` | 1,000,000 | 4 | +4764 | -1191.000 | 0/0/4 | +1376 |
| `wiki_graph_mtf64` | `bz2_9` | 500,000 | 4 | +2096 | -1048.000 | 2/0/2 | +2051 |
| `wiki_graph_mtf64` | `bz2_9` | 1,000,000 | 4 | -2951 | 737.750 | 4/0/0 | -549 |
| `wiki_graph_mtf64` | `lzma_6` | 500,000 | 4 | +3344 | -1672.000 | 0/0/4 | +1828 |
| `wiki_graph_mtf64` | `lzma_6` | 1,000,000 | 4 | +3280 | -820.000 | 0/0/4 | +960 |
| `xml_id_delta` | `bz2_9` | 500,000 | 4 | +1191 | -595.500 | 0/0/4 | +419 |
| `xml_id_delta` | `bz2_9` | 1,000,000 | 4 | +1886 | -471.500 | 0/0/4 | +550 |
| `xml_id_delta` | `lzma_6` | 500,000 | 4 | -4 | 2.000 | 3/0/1 | +40 |
| `xml_id_delta` | `lzma_6` | 1,000,000 | 4 | -188 | 47.000 | 4/0/0 | -32 |

## Interpretation

Negative archive deltas and positive gain rates are improvements over raw input under the same backend. The algorithm source/package cost is not counted in this proxy receipt. Backend disagreement, window regressions, or failure to clear 700 gross bytes per million at every tested scope prevents promotion.
