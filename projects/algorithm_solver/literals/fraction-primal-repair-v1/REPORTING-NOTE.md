# Reporting addition, 2026-10-23

The unpinned reporter now shows the seed and every feasible warm/cold witness's F, C, character fraction, total selections N, total actions, median/p90/p95 selections, and signed changes against the minimum-F seed. Entry counts and shares cover one-owner entries, near-whole entries and their intersection. Near-whole keeps the inherited threshold of at least 90% of any containing source. Shares use all dictionary entries, including unused entries and singletons. These are descriptive size/support statistics, not semantic reuse or legality tests.

All rows retain the actual minimum-F packet policy, with minimum-N then entry-ID tie-breaking. They are not minimum-N encodings. Metadata explicitly identifies lower fraction or lower F accompanied by higher N. No new search, source transformation, qualification, min-N counterfactual or admission claim is introduced.

Four new tests in the unpinned test_report_aux.py pass under the frozen Python. They cover threshold boundaries and unused-entry denominators, the fraction/N tradeoff, an actual synthetic minimum-F packet using three selections where minimum-N needs two, and complete invented 300-program report fixtures including all feasible witnesses and failure replacement. Syntax and diff checks pass. No private item 40 or item 35 inputs were read while the live experiment was running.

Audit note: tests were initially added to the existing test_report.py before its pin membership was checked. That file is pinned; it was restored byte-for-byte to its frozen hash, and the additions moved to the new unpinned auxiliary file. The transient edit is disclosed here. The final contract, all 124 execution code pins and all 10 runtime pins match the pre-edit snapshot. No frozen execution file or contract change remains. This reporting note does not assert a live-run outcome.

Before final run reporting, the cold-witness absence label was clarified to “no feasible output returned.” A time-limited solver that finds no feasible point does not establish model infeasibility; the seed proves coverage exists in this pool. Numeric solver status and all failure receipts remain unchanged.
