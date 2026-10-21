# Exact token-boundary proposals on the same 150 programs

The best measured input candidate uses **12,337 eight-bit selections**, median **74**, p95 **198**, worst **305**, **58.09%** single-character selection bits, and **22,296 dictionary-plus-packet bytes**. All 150 known programs remain represented with 256 entries and zero whole-program literals. This improves the 12,790-selection scale150 control by 453 selections and 477 package bytes. M1 remains unmet.

## Implemented change and controlled comparison

Acorn proposes exact slices at JavaScript token boundaries: one through five tokens, 2–96 UTF-8 bytes, supported by at least two distinct problems. Identifiers, constants, whitespace and punctuation are literal bytes. There are no parameter slots, free renaming or nonterminal expansion. Repeated variants of one problem do not inflate distinct-problem support. Mining produces 26,786 candidate strings from the same 1,006 qualified source alternatives.

Each round shortlists 48 lexical candidates by estimated savings on currently chosen programs, 24 AST fragments and 24 encoded-span fragments. It then scores their actual marginal effect with exact minimum-selection segmentation and source-variant reselection. Move acceptance uses exact add/remove/swap costs. The estimate only shortlists candidates; it never establishes the measured improvement.

A matched ablation uses the existing AST and encoded-span techniques alone, widened to 48 of each. Both arms start from the same scale150 dictionaries and qualified sources, with eight rounds, at most 2,400 legal moves and 768 ranking probes per width, and a 180-second wall limit per width. This separates token proposals from merely running the previous search longer. Source programs, tests and native qualification are unchanged; this is dictionary research only.

| Arm | Entries / bits | Selections | Median | p95 | Worst | Character bits | Package bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Scale150 control | 128 / 7 | 20,534 | 121 | 296 | 432 | 81.14% | 26,429 |
| Deeper AST/span | 128 / 7 | 20,229 | 121 | 296 | 432 | 80.79% | 26,238 |
| Token proposals | 128 / 7 | **20,155** | **117.5** | **292** | 432 | 79.09% | 25,532 |
| Token storage alternative | 128 / 7 | 20,215 | 118 | 292 | 432 | **78.73%** | **25,313** |
| Scale150 control | 256 / 8 | 12,790 | 77 | 205 | 309 | 60.43% | 22,773 |
| Deeper AST/span | 256 / 8 | 12,738 | 76.5 | 204 | 305 | 59.95% | 22,706 |
| Token proposals | 256 / 8 | **12,337** | **74** | **198** | **305** | 58.09% | 22,296 |
| Token storage alternative | 255 / 8 | 12,379 | 74 | 198 | 305 | **57.84%** | **21,907** |

The lexical arm beats the deeper AST/span arm by 401 eight-bit selections and 410 package bytes. This is a measured local-neighborhood result, not global optimality or proof that token proposals win on other populations. Searches stop when their tested neighborhood has no improving move; seven-bit token search uses 438 legal moves and 285 ranking probes in 20.76 seconds, eight-bit uses 1,935 and 665 in 70.17 seconds. Full ablation counters are retained in its independent audit.

## Costs and shared-subset tradeoffs

The eight-bit input candidate costs 98,696 payload bits, 6,150 framing bytes, zero padding, and 3,809 dictionary bytes. The storage alternative increases payload to 99,032 bits while shrinking the dictionary to 3,378 bytes. Decoder/interpreter/tooling storage is separate and unchanged; there is no model, cluster-selector or hidden helper injection. Human navigation/control cost is not measured by offline encoding.

| Eight-bit input arm | Original 100 selections | Shared 125 selections | New 25 selections | Full 150 |
|---|---:|---:|---:|---:|
| Scale150 control | 6,646 | 9,840 | 2,950 | 12,790 |
| Deeper AST/span | 6,678 | 9,835 | 2,903 | 12,738 |
| Token proposals | 6,660 | 9,635 | 2,702 | 12,337 |

The token candidate regresses the original 100 by 14 selections while improving shared 125 by 205 and new 25 by 248. The stored control remains available; no aggregate hides that regression. All constructor support from scale150 is still inside the charged source.

## Verification and limits

Each arm's independent forward scorer checks every chosen source against all alternatives. Each audit decodes 900 packets and verifies their bytes, hashes, selection optimality, quantiles, fallback fraction, entry limit and distinct-problem reuse. Across token and ablation experiments, **1,800 packets** pass. No source changed, so the existing native qualification is inherited by exact hashes rather than rerun as a misleading new solving result.

The exact 150 development IDs and 1,006 alternatives remain fixed. No protected examples or future-stage source/cases were opened. This measures offline representation, not autonomous problem-to-program composition. M1 still needs 400/500 frozen coverage, median at most 32, p95 at most 96, at most 10% character bits, and at most 256 entries with no whole solutions. The current native source style and fixed-string budget remain far above those cost gates; more round count alone is not an adequate strategy. Coordinated source rewrites and further already-qualified corpus expansion are the next independent tracks. At least 37 additional JavaScript admissions and a concrete frozen 500-problem population remain milestone dependencies, per the scale150 inventory.

Private token candidates, source alternatives, sequences, dictionaries, packets and full search traces are retained locally. The public package contains only methods, aggregate metrics and hashes. The scripts preserve executed task-local paths as provenance; reproducing requires the corresponding hash-bound private inputs. No live BITS dictionary, site release, or user-owned admission ledger changed.
