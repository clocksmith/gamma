# Exact marginal ranking of literal proposals

This successor improves candidate ranking while keeping all **674 qualified source
choices across the same 100 problems unchanged**. It compares estimated savings
with actual re-encoding and source reselection before choosing the shortlist.

[Contract](evidence/contract.json) · [Results and per-problem costs](evidence/report.json) ·
[Verification](evidence/verification.json) · [Prior DP-row comparison](../row-v1/README.md)

## The change

At each state, both routes form the same bounded union of up to 192 AST proposals
and 192 encoded-span proposals. Both use the same source choices, dictionary seed,
24-addition shortlist, deletion/swap/pair mechanism, objective and search limits.
Their subsequent states can differ.

The estimated route ranks fragment length savings multiplied by occurrence counts.
The exact route inserts each candidate provisionally, finds the shortest complete
encoding for every source alternative, then reselects the best source per problem.
It ranks by total selections, then complete package cost. A popular fragment in an
unselected, expensive source can therefore have zero marginal value.

Ranking probes may temporarily exceed the entry cap; they only estimate addition
value. Every actual admitted addition or swap stays within 128 or 256 entries.
The final decoder remains exact concatenation; no syntax or argument is supplied
for free. Whole-solution/body exclusions and distinct-problem sharing remain active.

## Matched result

| Arm | Estimated ranking | Exact ranking |
|---|---:|---:|
| Seven-bit selections | 11,746 | **11,558** |
| Seven-bit package | 15,989 B | **15,750 B** |
| Seven-bit median / p95 | 105.5 / 256 | **102.5 / 250** |
| Seven-bit character fraction | 78.01% | **76.93%** |
| Eight-bit selections | 7,016 | **6,963** |
| Eight-bit package | **13,948 B** | 14,005 B |
| Eight-bit median / p95 | 60 / **152** | **58.5** / 153 |
| Eight-bit worst | **230** | 234 |
| Eight-bit character fraction | 53.38% | 53.37% |

Estimated ranking finds no improving move in its tested neighborhood. Exact
ranking accepts two seven-bit moves and three eight-bit moves. It saves 188
seven-bit selections (1.60%) and 239 package bytes (1.49%). At eight bits it saves
53 selections (0.76%) while adding 57 bytes (0.41%) and worsening the tail.
The pre-DP heap control still has the smaller eight-bit package, 13,797 B.

This is a search improvement on exposed development sources, not an optimality,
novelty, compact-library qualification or autonomous-solving claim. Final character
use remains high. The predeclared objective prioritizes total selections; it does
not guarantee that p95, storage and worst-case input improve together.

## Costs and verification

The exact route scores 1,140 seven-bit and 1,519 eight-bit ranking probes. It takes
15.01 and 25.26 seconds, versus 3.80 and 5.11 seconds for the estimated routes.
Ranking itself accounts for 6.22 and 8.96 seconds. These are offline search costs,
not query latency. All routes stop because their tested neighborhoods contain no
further improving move, before the 120-second/1,600-trial limits.

Six focused checks compare marginal scores against a separate forward parser and
cover a misleading high-frequency alternate. The initial alternate was accidentally
shorter after substitution; that test expectation was corrected, and its original
fixture and diagnosis remain in the private run. The measured implementation did
not change during the run.

All **400 packets** independently decode to unchanged qualified source hashes.
A separate forward parser reproduces the minimum selection counts and selected
source alternatives. All **five accepted moves** independently replay. Native
execution is inherited from the hash-bound source receipts; no new program
execution or generalization result is claimed.

## Reproduce

Run test-ranking.py, then search.py with --parent pointing to the frozen row-v1
private run and --output pointing to a new private directory. The report records
source-pool, code, dictionary, manifest and trace identities. It preserves rejected
proposals and accepted moves in the private traces; the public report contains
only hashes, IDs and costs, not private sources or literal strings.

Next: reduce the high character fraction with shared control/binding structures,
and retain package/tail tradeoffs explicitly when selecting the next candidate.
Broader coverage still needs its frozen 500-problem contract; none of M1–5 is
completed by this representation-only comparison.
