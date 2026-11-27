# Shared definitions in normalized JavaScript

This CPU development experiment asks whether the price of storing a compound macro changes which macros a trainer buys, and whether those purchases repay their cost on other problem clusters. Both libraries can encode a nested call such as `Scan(n, Update(...))`. A flat library can also buy the fully expanded definition of every compound macro offered to the hierarchical trainer.

## Comparisons

1. **Header.** Serialize identical numbered, expanded definitions and identical calls twice. The flat header stores expanded bodies. The shared header can refer to earlier definitions. Require identical payload bytes under each fixed probability model, and decode both standalone archives to the same normalized ASTs.
2. **Probability model.** Fix library and calls. Compare general dispatch with dispatch conditioned on the calling template and hole, with training-only estimates and a common backoff. Charge all probability tables, framing and padding. Cross both models with both header formats. Report payload and table costs separately.
3. **Selection.** Give both trainers the same candidate definitions, binder semantics, ordering, search budget and access to both probability models. Select using complete fit-archive bytes. Compare their selected libraries on spent development problems with a plain AST and with each other. Keep each model and library fixed there. Count both purchased and actually invoked macros. Where the hierarchical trainer alone purchases a macro, measure the change in dev payload when re-encoding with its invocation disabled and its header still paid.

## Decision and scope

Use the existing A2 manifest to select 64 fit and 64 disjoint spent development problem lineages, one program per lineage, deterministically before parsing. A refusal counts against coverage. Every archive must independently reconstruct every target normalized AST. Program bytes in the original source language belong to a different fidelity target.

Report signed complete-byte differences for both mechanistic controls and the selected libraries. Record a positive development result for the purchase hypothesis only if the hierarchical library beats both baselines on complete bytes, buys a distinct macro, and its extra purchases reduce the dev payload. Record the measured direction and size even when the hypothesis fails. One-time dictionary and probability tables count once for the whole batch. Treat size crossovers computed from assumed rates as illustrations.

This experiment uses previously inspected inputs. The separate [frozen depth-one study](../a2-recursive-frames-v1/PREREGISTRATION_DEPTH1.md) has its own input contract and decision.

## Development result

Shared definitions saved **73 bytes** when both formats could evaluate the same 97 candidate libraries. Each selected the same 13 definitions and general dispatch prior on fit data. Both encoded 801 nested calls on the 64 development programs. The two tested library budgets, 512 and 2,048 bytes, admitted the same winner. Plain AST consumed 20,671 complete bytes.

| Fixed calls and library | Library bytes | Probability tables | Payload bytes | Complete bytes |
| --- | ---: | ---: | ---: | ---: |
| Expanded definitions, general prior | 398 | 495 | 18,585 | 19,493 |
| Shared definitions, general prior | 325 | 495 | 18,585 | 19,420 |
| Expanded definitions, hole prior | 398 | 757 | 18,334 | 19,504 |
| Shared definitions, hole prior | 325 | 757 | 18,334 | 19,431 |

Each archive also pays 15 framing bytes. Hole conditioning saved 251 payload bytes and cost 262 extra table bytes. Under the initial greedy search, expanded definitions stopped after 30 candidate-library trials and shared definitions after 84. The resulting 475-byte advantage included nine extra macros that were used on 62 of 64 development problems. Inlining all nine and refunding their definitions added 680 complete bytes. On the common candidate list the flat trainer also purchased all nine. The distinct-purchase hypothesis missed its development gate.

Scopes and nested arguments were checked against named normalized ASTs and normalized bytes. Both arm formats use the same DEFLATE side stream for auxiliary data. The sample contains 64 fit and 64 spent development problem lineages. The [receipt](dev_receipt.json) records actual archive hashes, candidate order, per-lineage usage, ablations and measured work.

Run `python3 -m unittest discover` for the codec and binder checks and `python3 replay.py check` to reproduce the complete receipt apart from wall-clock time.
