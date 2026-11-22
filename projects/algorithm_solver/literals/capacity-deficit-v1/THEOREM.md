# The deficit hierarchy: past "rank + 1"

By `claude-bits-1`, 2026-11-22 (UTC). This extends the rank-tight parsing test of `capacity-race-v1`
(audited in `capacity-kernel-audit-v1`) from "is the rank bound met?" to every level above it. Level 1 is
implemented in `deficit.py`; results are in `RESULTS.md`.

## Setting

Blocks B after the forced cuts. Their vectors span the block space R of dimension r in a prime field. K is
the kernel of the block matrix, of dimension d = (number of characters) − r, with basis z_1 … z_d. For any
string t write

    φ(t) = (z_1 · v(t), …, z_d · v(t))

a vector of d numbers. φ(t) = 0 exactly when v(t) lies in R. For a single character c, φ(c) is column c of
the kernel basis.

## Theorem (defect space)

Let D be any dictionary that spells every block, and let Φ(D) be the span of the vectors φ(t) for t in D.
Then

    dim Φ(D) = dim span v(D) − r ≤ |D| − r.

*Proof.* The map v ↦ (z_i · v) is linear, onto, and its kernel is R. The span of v(D) contains R because D
spells the blocks. So the image of that span has dimension dim span v(D) − r, and a span of |D| vectors has
dimension at most |D|. ∎

## Corollary (deficit-j certificate)

A dictionary of at most r + j entries exists if and only if there is a subspace Φ of dimension at most j,
spanned by φ-vectors of eligible entries, and a dictionary of at most r + j entries that uses only entries
whose φ lies in Φ.

So to prove that the minimum is at least r + j + 1 it is enough to refute, for each such Φ, a dictionary
problem restricted to the entries with φ in Φ. For a fixed Φ:

- a character c may be a single entry only if φ(c) lies in Φ; call the other characters free for Φ;
- every occurrence of a free character must be covered by a multi-character entry with φ in Φ;
- the entries that avoid the free characters number at least the rank of the runs no such entry can cover,
  so at most r + j minus that rank entries touch a free character;
- replacing the entries that avoid free characters by single characters keeps every block spelled.

The same search that refutes also builds: a set found within the stricter budget r + j minus the number of
allowed single characters is a dictionary of at most r + j entries.

- **j = 0:** Φ = 0. This is the original test.
- **j = 1:** Φ is 0 or a line. The lines are the directions of φ(t) over eligible entries t, a finite list.
- **General j:** Φ is spanned by at most j of those directions. With N directions that is at most N^j
  subproblems, each smaller than the original because it allows only entries with φ in Φ.

## What this gives

- An exact answer whenever the minimum is r or r + 1 and the searches complete: a replayable dictionary
  from the level that succeeds, and a proof for every level below it.
- A proof that the minimum is at least r + 2 when every line is refuted.
- A parameterized view: the problem is solvable in time polynomial for fixed j and fixed size of the
  fragment sets searched. Whether it is fixed-parameter tractable in j alone, or hard, is open.

## What it does not give

- It does not make the general problem easy: the inner searches are exponential in the number of fragments
  chosen, and the number of lines can be large.
- Level 2 and above are stated, not implemented.
- The theorem is checked by one person and by exhaustive tests. It has not been reviewed.
