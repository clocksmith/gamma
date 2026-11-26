# Review of the leaf-soundness argument (2026-11-26)

Reviewer: the BITS lane owner, who did not write `PREREGISTRATION.md`. It is a reading of
"Leaf soundness" (lines 63 to 170) against `../capacity-ladder-v1/THEOREM.md`. Nothing was run, and
`PREREGISTRATION.md` is unchanged.

## Verdict

The argument is sound as written. The r + 4 ceiling is derived correctly. The O1 candidate (packing
inequalities) is also sound, which was the one step the author marked as unreviewed. Details follow,
with three points the implementation must get right.

## Step by step

- **Lemma 1 (budgeted tree).** At the root, |D| ≤ r + J gives dim Φ(D) ≤ J by the defect-space
  theorem, so D ∈ C_T(0, J). In the step, D covers the uncoverable occurrence o with some e ∈ D. By
  uncoverability φ(e) ∉ Φ, so Φ + ⟨φ(e)⟩ ⊆ Φ(D) and dim Φ(D) ≤ dim(Φ + ⟨φ(e)⟩) + (j − 1). The child
  receives the same D, so |D| ≤ T is preserved. Sound. The children range over every eligible e
  through o, not only those in some D, as Theorem 2 requires.
- **Lemma 2 (potentials).** A parse of block b is a chain 0 = i_0 < … < i_k = |b|. Its steps are
  occurrences at distinct (b, i), so each is counted once in its entry's charge. Π_b telescopes and is
  at most the sum of positive parts. Charges are non-negative, so Σ_{t∈D} c_t ≤ S_{|D|} ≤ S_T for
  D ⊆ P with |D| ≤ T. Sound for any integer potentials. Blocks are distinct, and Π sums over distinct
  blocks too, so a repeated block is neither double-counted nor missed.
- **Lemma 3.** Immediate from Lemma 2, given the premise C_T(Φ, j) ⊆ {D ⊆ P}.
- **L0.** Φ ⊆ Φ(D) and dim Φ(D) ≤ dim Φ force Φ(D) = Φ, so every entry of D maps into Φ. Sound.
- **L1.** e covers o, φ(e) ∉ Φ, and dim Φ(D) ≤ dim Φ + 1 force Φ(D) = Φ + ⟨φ(e)⟩. Hence
  D ⊆ E(Φ + ⟨φ(e)⟩) for that e, and D lies in the union. Sound.
- **Lg.** P = E is trivially sound. The leaf's test does not depend on its node, so it closes anywhere
  exactly when it closes at the root. "Then arm 1 already proves the bound" therefore needs arm 1 to
  use the same potentials and the same sorted-sum test S_T. Line 282 says it does. If arm 1 ever used
  the ratio Π / max c instead, an Lg leaf could beat it, and P1 to P10 would mislabel that win.
- **Terminal stuck check.** At spare 1, if every child Φ + ⟨φ(e)⟩ has an uncoverable occurrence,
  each child satisfies N(·, 0) by item 1 of Theorem 2. Sound.
- **The ceiling.** Non-Lg leaves sit only at spare 0 or 1, and branching stops at depth 2 (line 288).
  So J − 2 ≤ 1, J ≤ 3 and the bound is at most r + 4. This ceiling comes from the depth-2 cap together
  with O1 being open. It is not a limit of the theorem. If O1 is discharged, the cap still has to be
  lifted to pass r + 4.

## O1: the packing candidate is sound

Claim: let S ⊆ E \ E(Φ) have images in F_p^d / Φ that are (k + 1)-wise linearly independent, meaning
any k + 1 of them are independent. Then every D in C_T(Φ, k) has |D ∩ S| ≤ k.

Proof. Φ ⊆ Φ(D) and dim Φ(D) ≤ dim Φ + k give dim(Φ(D)/Φ) ≤ k. The images of D ∩ S lie in
Φ(D)/Φ. If |D ∩ S| ≥ k + 1, any k + 1 of them are independent there and span dimension k + 1 > k, a
contradiction. ∎

Using it in a leaf: with P = E and side constraints |D ∩ S_i| ≤ k, Lemma 3 holds with S_T replaced by
the largest Σ c_t over D ⊆ E with |D| ≤ T and every |D ∩ S_i| ≤ k. Any upper bound on that maximum
is sound. For one S, or for disjoint ones, it is the sorted sum with at most k taken from each S_i.
Overlapping S_i need a relaxation, for example keeping only one family. That makes spare ≥ 2 leaves
possible in principle. Whether they ever close is empirical and belongs in a separate registration,
as O1 says. Checking (k + 1)-wise independence costs one rank test for each (k + 1)-subset. A
sufficient check that costs less: the images are columns of a matrix whose every k + 1 columns are
independent. For k = 1 that only means pairwise non-parallel.

## What the implementation must get right (on top of O2 to O4)

1. **E exactly.** Lemma 3's premise and L1's union are only as good as the verifier's own enumeration
   of E: single characters, plus strings of at most 160 bytes in at least two texts that are not a
   whole text. Charges must be recomputed for every t ∈ P, not read from the certificate, because an
   omitted high-charge entry makes S_T too small and the bound unsound. On families of 3 to 6 files of
   at most 4,000 bytes this is a few million candidates. The capped checker's megabyte problem does
   not arise.
2. **One T everywhere** (O2), and the unbudgeted `capacity-ladder-v1/check_certificate.py` must not be
   reused for hybrid certificates. It accepts trees without a budget, which is right only for pure
   trees.
3. **The positive control** (line 323) should include the ss case from line 136, a dictionary holding
   s and ss. That is the concrete way the tempting reading fails, so the audit must contain an instance
   where it changes the answer.

## Status

The hybrid run stays paused until the owner says otherwise. This review discharges no kill rule and
changes no forecast. It confirms that writing `hybrid.py` and `verify_hybrid.py` would rest on a sound
argument, and that O1 has a sound candidate for a later registration.
