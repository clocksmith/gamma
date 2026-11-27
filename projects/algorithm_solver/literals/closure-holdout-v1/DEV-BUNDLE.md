# Development test: can a closure-preserving bundle rule match open token gain in training?

Written and committed before any bundle chain was built. **Development only**: training files (CodeNet `primary`,
400 files) for the decision; `dev` tokens are reported as description. No held-out set is opened and no claim of the
paper's held-out results changes. A miss measures the price of this bundle rule; it does not show what caused the
held-out reversal.

## Arms (all: policy `s1-whole`, L = 16, same 171-byte singleton inventory, exact shortest-path parser)

| Arm | Candidates at each step | Score | Trainer |
| --- | --- | --- | --- |
| open | any fragment | Delta(w) | exact greedy (`out/exact/exact-entry-s1-whole.txt`) |
| pair | closed: w = uv, u, v in V | Delta(w) | exact greedy (`exact-closed`) |
| bundle | for each fragment w: the missing entries B(w) of the left chain of prefixes along one minimum V-spelling t_1..t_s (t_1t_2, t_1t_2t_3, ..., w); s = 2 gives B = {w}, a pair | Delta(B) / \|B\| | lazy greedy (heuristic) |
| open-byte | any fragment | Delta(w) / (1 + \|w\|) | exact greedy (`exact-byte`) |
| pair-byte | closed | Delta(w) / (1 + \|w\|) | exact greedy (new mode `exact-closed-byte`) |
| bundle-byte | as bundle | Delta(B) / sum over B of (1 + \|e\|) | lazy greedy (heuristic) |

Delta(B) is the exact drop in training tokens from adding all of B at once. Bundle entries are written in prefix order,
so every prefix of a bundle chain is closed (each entry is the concatenation of two earlier entries or bytes).
pair-byte is the control for bundle-byte: it separates buying bundles from charging for size.
Calibration of the heuristic trainer: the bundle engine with bundles capped at one entry is lazy pair selection; its
gap to exact pair selection bounds how much the lazy trainer costs.

## Budgets and tolerance (fixed now)

- **Equal slots:** 84 and 3,924 fragments. Reference: open, 135,219 and 39,204 training tokens.
- **Equal serialized bytes:** fragment bytes sum(1 + |e|) of 566 and 43,480 (open's at 84 and 3,924 fragments). Each
  arm is its longest chain prefix within the budget. Reference: the fewer training tokens of open and open-byte.
- **Match:** an arm matches if its training tokens are at most 1.02 x the reference at a budget (equal slots:
  137,923 and 39,988).

## Predictions (made before running)

1. bundle misses at 3,924 slots (slot-tax corollary in NORMALIZED-PAIRS.md).
2. bundle misses at 84 slots.
3. At equal bytes, bundle-byte is closer to the reference than bundle is at equal slots, and still misses at 43,480 bytes.
4. bundle uses fewer training tokens than pair at 3,924 slots (it can choose every pair); if not, the heuristic trainer
   is the limit and the test is inconclusive.

## What follows

A miss: report the price of this bundle rule at each budget. A match at both sizes of a budget: the bundle rule becomes
eligible for a held-out comparison, to be preregistered separately; nothing is run on held-out data here.
