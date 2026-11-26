# Do checkable trees close the gaps the strongest prior bound leaves open?

**Status: preregistered, not run. Not frozen.** The registration binds only once `SHA256SUMS-CORPUS` exists
and is committed. That file does not exist yet, because no corpus has been selected. No package has been
downloaded, no code for it has been written, and no method has been run on any new family.

- `PREREGISTRATION.md` covers the questions, the leaf-soundness argument and its open obligations, the hard
  caps on proof size and verification time, the seeded selection rule for 40 non-saturated families, the arms,
  checking, kill thresholds, predictions and the implementation plan.

The primary question is whether pure defect trees and a hybrid tree with Lagrangian dual leaves close
minimum-string-cover gaps on unseen code that the strongest prior bound leaves open. That prior bound is the
largest of block rank, the level-0/1 ladder, the Lagrangian dual and HiGHS. The hybrid certificate is the
secondary arm.

Everything in the implementation plan is marked not yet built. Nothing here is a result.
