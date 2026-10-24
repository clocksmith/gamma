# packing-applicability-v1: does item 71's packing count ever bind on the original fit sources? (board item 76, T2)

## Question

Item 71 (`b891f5390`, invented measurement `c229ea885`) replaces an entry's occurrence count m_ep in source p by
n_ep = min(m_ep, floor(N_p / len(e))). Both the owner refinement and the global one sum this per-source term.
**n_ep < m_ep holds exactly when m_ep · len(e) > N_p**: the overlapping occurrences of e must cover more characters
than the source has, which is possible only for self-overlapping strings in long periodic runs. The invented fixture
`repeated_one_owner_12k` was built to have such runs, and 97.8% of its owner endpoints bind. Real code may have none.

If no (source, substring) pair in a cohort satisfies m · len > N, then n = m for every entry, owner or shared. Item
71's refinement then equals items 63 and 66 exactly on that cohort, and no original-input protocol for item 71 is
needed. This stage measures that. It is a design-stage diagnostic, not a certificate run.

## Inputs and method

- **Sources.** Item 63's two original fit cohorts, read from the private work directory and pinned by SHA-256:
  - R: `binding-descent/run-v1/control-256/fit-sources.json`, `c0a4b1b5…`;
  - naming: `scope_joint-256/fit-sources.json`, `4785b837…`.
  Each has 300 sources, and their character totals must equal item 63's `full_shape`: 76,107 and 76,033.
  These are consumed development fit data. No validation, held-out or protected data is read.
- **Method.** [applicability.py](applicability.py) `binding()` examines **every** substring of length 2 or more of every
  source, counting overlapping occurrences in m. That is a superset of the allowed class, since bans and ownership only
  remove entries. It counts the pairs with m · len > N and records the largest m · len / N.
- **Tests.** [test_applicability.py](test_applicability.py) compares `binding()` with a brute-force count of
  `min(m, N // len) < m` on 300 random small texts, plus known cases. 2 of 2 pass.

## Decision rule and prediction

- **Zero binding pairs in both cohorts** means item 71 equals items 63/66 on the original fit, owner and global alike.
  An original-input item 71 protocol is then unnecessary, and that line closes as provably null there.
- **Any binding pair** means the protocol stays a candidate. Only the counts are recorded; no bound is computed here.
- **Prediction A1:** zero binding pairs in both cohorts. I expect this, because JS solutions are not dominated by
  periodic runs.

## Resources and rules

- One process on core 0, single-threaded. Evidence holds counts and hashes only.
- **Cross-review.** A fresh-context Claude subagent stands in for codex, who is out until 2026-10-30.
- No training, publication of private sources, protected opening, deployment, or ledger, claim or catalog write.
