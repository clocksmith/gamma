# Pre-registration: do checkable trees close the gaps the strongest prior bound leaves open?

Drafted on 2026-11-26 (UTC), before any corpus for it exists and before any line of its code is written.
**Nothing has been run.** No package has been downloaded, no rank, bound or dictionary has been computed on any
new family, and the selection rule below has not been executed. This file binds only once it is committed
together with `SHA256SUMS-CORPUS` (see "Order of events"). Until then it is a draft and may change.

Paths below are relative to this folder. `file:line` citations are to files as committed at the time of writing.

## Questions

1. **Primary.** On unseen non-saturated families (block rank r below the alphabet |Σ|), do *checkable trees*,
   meaning pure defect trees and the hybrid of question 2, routinely close gaps that the strongest prior bound
   leaves open?
2. **Secondary.** Does a hybrid certificate, a shallow defect tree with Lagrangian dual leaves where its fan-out
   is too large, certify bounds strictly above max(standalone Lagrangian dual, standalone defect tree), quickly
   enough to check, and never wrongly?

The rule is the witness rule W of the earlier races: a single character is always eligible unless it is a whole
text; a longer entry must occur in at least two texts and be at most 160 UTF-8 bytes; no whole text.

## Exact claims, and what is measured versus what is forecast

**Strongest prior bound**, per family: the maximum of

- the block rank r;
- the ladder at levels 0 and 1: `min(L2, r + 2)`, where L2 is the lower bound of arm 2 below. The ladder climbs
  level by level, so this is what it proved at levels 0 and 1. Search-backed bounds count here;
- the standalone Lagrangian dual (arm 1);
- the HiGHS bound (arm 3): its final MIP dual bound, rounded up, *as claimed by the solver*. A claimed bound counts
  in the prior because that is the conservative choice for the primary question. A certified-only prior (root
  linear-program dual, exactly checked) is reported beside it.

**Best upper bound**: the smallest dictionary any arm returns that replays (see "How answers are checked"), or
|Σ|.

**Gap**: the family is open under the prior when prior < best upper bound. G is the set of such families.

**Checkable-tree bound**: the largest bound certified by a pure defect-tree certificate of arm 2 or a hybrid
certificate of arm 4 that meets every hard constraint below and that the independent verifier accepts. A
certificate that breaks a constraint counts as no proof. A family with no such certificate gets r.

On each family in G:

- **shrunk**: checkable-tree bound > prior;
- **closed**: checkable-tree bound = best upper bound (it then also exceeds the prior).

**Primary claim (C1).** Checkable trees close at least one third of G, and at least 3 families. If |G| < 3 the
primary question is reported as **not answerable on this corpus**; that outcome is itself recorded, because it
would mean the prior bounds already settle nearly everything.

**Secondary claim (C2).** The hybrid's certified bound is strictly above max(arm 1, arm 2) on at least 8 of the
40 families (20 %, the meaning of "a meaningful share" here), the median independent verification time of its
non-trivial certificates is at most 2 s, it gives no wrong bound anywhere, and kill condition (c) does not fire.
For "max(arm 1, arm 2)", arm 2's bound includes search-backed levels. That is the conservative choice against the
hybrid.

**Measured** in the run: every arm's lower bound, certificate, dictionary, wall and CPU time per family; every
certificate's node count, byte size and verification time; the counts |G|, shrunk and closed; the hybrid's strict
wins and which leaf kind produced each; the audit counts. **Forecast**: the predictions P1 to P10. **Not
claimed**: anything about presses, encoded bits, other rules, or other implementations of the methods.

## Leaf soundness

### Setting

As in `../capacity-ladder-v1/THEOREM.md:6-14`. E is the set of eligible entries, B the distinct forced blocks.
No eligible entry crosses a forced cut, so a dictionary spells every text exactly when it spells every block.
Everything is in one prime field F_p with polynomial base β: v(t) = Σ_k β^k e_{t_k}, kernel basis z_1 … z_d of
the block matrix, φ(t) = (z_i · v(t))_i. For a subspace Φ of F_p^d write E(Φ) = {e ∈ E : φ(e) ∈ Φ}, and
Φ(D) = span φ(D). The defect-space theorem (`../capacity-deficit-v1/THEOREM.md:16-27`; restated in
`../capacity-ladder-v1/THEOREM.md:13-14`) gives dim Φ(D) ≤ |D| − r for every D that spells B. Its proof uses only
linearity and that the kernel of v ↦ (z_i · v) is the block space R, so it holds in any prime field, with r the
rank in that field.

### Step 1: the node claim must carry the budget

Theorem 2 of `../capacity-ladder-v1/THEOREM.md:24-38` (the defect tree) is about N(Φ, j): "no D with Φ ⊆ Φ(D) and
dim Φ(D) ≤ dim Φ + j". A Lagrangian dual bounds the *number* of entries, |D|. A lower bound on |D| never implies
anything about dim Φ(D). So no dual bound can establish the unbudgeted N(Φ, j), and a leaf cannot be attached to
the tree as stated. The tree has to be restated with the budget.

Write C_T(Φ, j) for the set of dictionaries D that spell B with |D| ≤ T, Φ ⊆ Φ(D) and dim Φ(D) ≤ dim Φ + j, and
N_T(Φ, j) for "C_T(Φ, j) is empty".

**Lemma 1 (budgeted tree).** Theorem 2 holds with N replaced by N_T, the same T at every node. With root (0, J) and
T = r + J, N_T(0, J) implies that the minimum is at least r + J + 1.

*Proof.* The uncoverable-occurrence lemma (`THEOREM.md:16-22`) does not mention |D|. In the induction step the
dictionary D handed to a child is the same D, so |D| ≤ T still holds. At the root, any D with |D| ≤ r + J has
dim Φ(D) ≤ J by the defect-space theorem, and 0 ⊆ Φ(D), so D ∈ C_T(0, J). ∎

The search in `../capacity-ladder-v1/ladder.py:479-541` already carries the budget (`prove(space, j, total)`).
The certificate schema and checker of `capacity-ladder-v1` do not (`check_certificate.py:10-16`): they check the
unbudgeted claim, which is right for a pure tree and wrong for a tree with dual leaves. The new schema must
record T once and the verifier must test every leaf against that T.

### Step 2: the potential bound

**Lemma 2 (potentials).** Let P ⊆ E, and give every block b integer potentials π_b(0), …, π_b(|b|). For t ∈ P
let its charge be

    c_t = Σ over every occurrence (b, i) of t in a block of B of max(0, π_b(i + |t|) − π_b(i)),

counting every occurrence, including several in one block. Let Π = Σ_b (π_b(|b|) − π_b(0)) and let S_m be the
sum of the m largest charges in P. Then every D ⊆ P that spells B satisfies Π ≤ Σ_{t∈D} c_t ≤ S_{|D|}.

*Proof.* Take D's parse of b. The potential differences along the parse telescope to π_b(|b|) − π_b(0), each is
at most its positive part, and each parse step is an occurrence of an entry of D, so it is counted in that entry's
charge. Sum over the blocks. The last inequality holds because charges are non-negative. ∎

No condition on the potentials is needed: any finite integers work, and the solver only has to find good ones.
This is the exact check of `../capacity-lagrangian-race-v1/canzar_lagrangian.py:120-173` with its ratio
Π / max c replaced by the sorted sum. The sorted sum is never weaker, since S_T ≤ T · max c.

**Lemma 3 (leaf).** Suppose every D in C_T(Φ, j) satisfies D ⊆ P. If S_T < Π, or some block has no parse by
entries of P, then N_T(Φ, j) holds.

*Proof.* A D in C_T(Φ, j) would have D ⊆ P and |D| ≤ T, so Π ≤ S_{|D|} ≤ S_T, a contradiction. If a block has no
parse by P, no D ⊆ P spells B. ∎

### Step 3, the crux: which P is allowed

Lemma 3 is only as good as the premise "every D in C_T(Φ, j) uses only entries in P". Three choices of P satisfy
it:

- **L0, spare j = 0: P = E(Φ).** If Φ ⊆ Φ(D) and dim Φ(D) ≤ dim Φ, then Φ(D) = Φ, so φ(e) ∈ Φ for every e in D.
- **L1, spare j = 1, at a node with an uncoverable occurrence o: P = ∪_e E(Φ + ⟨φ(e)⟩)**, the union over *every*
  eligible e through o: the single character at o when it is eligible, and every eligible substring of the block
  through o. D covers o with some e ∈ D. By uncoverability φ(e) ∉ Φ, so Φ + ⟨φ(e)⟩ ⊆ Φ(D), and
  dim Φ(D) ≤ dim Φ + 1 = dim(Φ + ⟨φ(e)⟩). Hence Φ(D) = Φ + ⟨φ(e)⟩ and D ⊆ E(Φ + ⟨φ(e)⟩) ⊆ P.
- **Lg, any other node: P = E**, no restriction. This leaf closes only if the global dual already exceeds T.

**The tempting reading is not sound.** "All entries have φ in Φ′, plus k further dimensions" must not be
implemented as "entries of E(Φ′) plus at most k entries outside it". One extra dimension can carry any number of
extra entries. For an eligible s whose square ss is also eligible, v(ss) = (1 + β^{|s|}) v(s), so φ(ss) is a
multiple of φ(s). A dictionary holding both spends two entries outside E(Φ′) on one new dimension. In general the
defect-space theorem bounds dimension by count, never count by dimension. The restricted problem therefore leaves
out dictionaries that are in C_T(Φ′, k), so its bound is not a bound on C_T(Φ′, k).

The other reading, "D ⊆ E(Φ′ + W) for some W of dimension at most k", is the corollary of
`../capacity-deficit-v1/THEOREM.md:29-35`. It is sound, but for k ≥ 1 the union over W is all of E. As one dual
it restricts nothing, and split per W it is the wide enumeration the tree was built to avoid. L1 is the one case
where an uncoverable occurrence makes the union small enough to matter.

### Consequence for this registration (derived, not forecast)

Leaves at spare 2 or more, and at spare 1 without an uncoverable occurrence, can only be Lg. An Lg leaf closes
exactly when the global dual beats T, and then arm 1 already proves the bound. So whenever the hybrid's bound
exceeds arm 1's, it comes from a tree of at most two branching levels with terminal stuck checks, L0 or L1 below.
That means root spare J ≤ 3, and the bound is at most r + 4. Arm 2 at `max_level = 3` also stops at r + 4. **The
hybrid can beat both only on families where arm 2 stalls below r + 4 and arm 1 is below the hybrid.** A strict win
above r + 4 that does not come from arm 1 is a bug, and work stops.

### Open obligations, to settle before implementation

- **O1 (open, the main one).** No sound entry restriction is known for leaves at spare k ≥ 2, or at spare 1
  without an uncoverable occurrence. One candidate, *not part of this registration*: packing inequalities. If S
  is a set of entries outside E(Φ) whose images in F_p^d / Φ are (k + 1)-wise linearly independent, then every D
  in C_T(Φ, k) has |D ∩ S| ≤ k, because Φ(D) = Φ + span φ(D \ E(Φ)) when Φ ⊆ Φ(D). The argument looks right to
  me but has not been reviewed. Whether the cuts help, and how cheaply the independence can be checked, is
  unknown. Discharging O1 is what would lift the r + 4 ceiling. It needs its own registration.
- **O2 (settled in argument; must be built).** The schema binds one T. The verifier checks that every child
  carries spare − 1, that L0 appears only at spare 0, that L1 appears only at spare 1 at a node whose stated
  occurrence it has itself confirmed uncoverable, and that every leaf's S_T < Π is computed against the root's T.
- **O3 (settled).** One field throughout. The verifier recomputes r in the certificate's prime. The ladder picks
  the field with the larger rank (`../capacity-ladder-v1/ladder.py:104-108`), which is fine, but the verifier
  must not mix fields.
- **O4 (settled; must be built).** L1's union must be recomputed by the verifier from E, not read from the
  certificate. Membership φ(e) ∈ Φ + ⟨φ(e_i)⟩ is a rank test in F_p. The single character at o is in the list only
  if it is not a whole text, as in `../capacity-ladder-v1/check_certificate.py:104-106`.
- **O5 (open, about arm 3, not soundness).** As far as I know, the HiGHS bundled with SciPy 1.18.0 exports no
  checkable proof of a MIP dual bound or of MIP infeasibility. Confirm this before implementation. If there is no
  such export, arm 3's bound above its exactly checked root dual is recorded as *claimed*.

## Hard constraints on proofs (fixed now, not outcomes)

Every certificate, from arm 2 or arm 4, counts as a proof only if all three hold. Otherwise it is **no proof**,
and the family's checkable-tree bound falls back to the best certificate of that family that does meet them, or
to r.

| Constraint | Cap |
| --- | ---: |
| Nodes (internal nodes, terminal stuck checks and leaves, counted together) | 5,000 |
| Bytes, canonical JSON (`separators=(',', ':')`, UTF-8, uncompressed) | 2,000,000 |
| Independent verification, wall time on one core, one run, killed at the cap | 30 s |

For comparison only: the PY-3 tree of `capacity-ladder-v1` has 4,141 nodes and 8.9 MB
(`../capacity-ladder-v1/real-corpora.json:257`, `verify_stored.py:9`), so it would count as no proof here. The
A08 tree has 12 nodes and 12 KB (`RESULTS.md:48`).

The hybrid's secondary claim (median ≤ 2 s) and kill condition (b) (median > 5 s) are measured *within* these caps.
A certificate killed at 30 s enters the median at 30 s.

## Corpus: 40 new non-saturated families

### Sources (pins)

Packages at exact versions. The selector checks each version from the package's own metadata and records the
SHA-256 of each archive it read in `source-pins.json`. Per source: subtree, one extension.

| Source | Pin | Subtree | Extension | Licence |
| --- | --- | --- | --- | --- |
| ramda | npm `ramda@0.30.1` | `src` | `.js` | MIT |
| underscore | npm `underscore@1.13.7` | `modules` | `.js` | MIT |
| d3-array | npm `d3-array@3.2.4` | `src` | `.js` | ISC |
| d3-shape | npm `d3-shape@3.2.0` | `src` | `.js` | ISC |
| d3-scale | npm `d3-scale@4.0.2` | `src` | `.js` | ISC |
| core-js | npm `core-js@3.39.0` | `modules` | `.js` | MIT |
| graphql | npm `graphql@16.9.0` | `` (whole package) | `.js` | MIT |
| eslint-plugin-react | npm `eslint-plugin-react@7.37.2` | `lib/rules` | `.js` | MIT |
| fp-ts | npm `fp-ts@2.16.9` | `es6` | `.js` | MIT |
| dayjs | npm `dayjs@1.11.13` | `esm/locale` | `.js` | MIT |
| mathjs | npm `mathjs@13.2.0` | `lib/esm/function` | `.js` | Apache-2.0 |
| networkx | PyPI `networkx==3.4.2` (wheel) | `networkx/algorithms` | `.py` | BSD-3-Clause |
| pygments | PyPI `pygments==2.18.0` (wheel) | `pygments` | `.py` | BSD-2-Clause |
| django | PyPI `django==5.1.3` (wheel) | `django` | `.py` | BSD-3-Clause |
| lua | release tarball `lua-5.4.7.tar.gz` | `src` | `.h` | MIT |

If a pin cannot be obtained, its version does not match, or its subtree is absent, that source is **dropped**.
The drop is written in `selection-log.json` before any method runs, and no substitute is added. The licences
above are as I remember them and are confirmed from each package at freeze time.

### Exclusions

- **Packages.** None used by `../matched80-v1` to `-v3`, `../capacity-boundary-v1`, `../capacity-deficit-race-v1`,
  `../capacity-race-v1`, `../capacity-lagrangian-race-v1` or the 59 corpora of `../capacity-ladder-v1`. That rules
  out CPython, three, rxjs, lodash and lodash-es at any version, @babel/runtime, ajv, eslint, zod, caniuse-lite,
  date-fns, GGML, FFmpeg, Cairo, Brotli, semver, PostCSS, protobufjs, Undici and this owner's own repositories.
  Also none of the sources named in `../fresh-short-records-v1/manifest.json`. That rules out, among others,
  webpack, sympy, babel, prettier, rollup and curl, so this public corpus cannot touch that lane's material. Its
  sealed test sources cannot be checked. The selector must not read its custody directory.
- **Files.** No file whose bytes have a SHA-256 equal to any file or program recorded in those folders (the
  matched80 programs via `../scale-v2/generated/manifest.json`), and no program whose text equals one of theirs.
- Directories named `node_modules`, `__pycache__`, `site-packages`, `test`, `tests`, as in
  `../capacity-deficit-race-v1/select_instances.py:25`.

### Selection rule (`select_instances.py`, seed `capacity-hybrid-certificate-v1/2026-11-26`)

1. Per source, list the directories under its subtree (recursive) holding at least six files of its extension
   between 300 and 4,000 bytes that decode as UTF-8 and are not excluded. Sort them, then shuffle with
   `random.Random(f'{SEED}/{source}')`.
2. Per source, a candidate stream as in `../capacity-deficit-race-v1/select_instances.py:111-134`: cycle through
   the shuffled directories, draw a size from {3, 4, 6}, and take a run of that many files consecutive in name
   order among the directory's unused files, at a seeded offset. Skip a run with two identical texts. Every file of
   an *examined* candidate is marked used, whether it is accepted or not.
3. Round-robin over the sources, in an order shuffled with `random.Random(f'{SEED}/order')`. Each turn takes the
   source's next candidate and computes **only** its alphabet, its forced blocks and its block rank in both fields
   of `../capacity-ladder-v1/ladder.py:28`, with r the larger of the two. Nothing else is computed. The candidate
   is accepted if r < |Σ| and its source has fewer than 4 accepted families.
4. Stop at 40 accepted families. A source is exhausted after 200 examined candidates or when it has no unused run
   left. If every source is exhausted before 40, this registration is void and a new one is written. Nothing is
   added by hand.
5. Output: `instances.json` with the texts embedded, licences and pins (no local paths), and `selection-log.json`
   with every examined candidate (source, directory, files with SHA-256, alphabet, rank, accepted or not, and why).

The selector computes rank because "non-saturated" cannot be decided without it. Rank is not an arm here, and it
is recomputed independently during checking. The selector's author also wrote this registration. The rule is
mechanical and can be rerun from the pins.

### Freeze

`SHA256SUMS-CORPUS` lists `PREREGISTRATION.md`, `README.md`, `select_instances.py`, `instances.json`,
`selection-log.json` and `source-pins.json`. It is committed before any arm runs on any new family. The registration
binds from that commit.

## Arms

Each call is its own process. The wall limit is **60 s per family per arm** on **one CPU core**: CPU affinity
where the platform supports it, and in every case a recorded CPU time of at most 1.05 × wall. One family runs at a
time. Spend is **$0**: no model calls and no paid compute.

| Arm | What runs | Lower bound it reports |
| --- | --- | --- |
| 0. Rank | Forced cuts and block rank (both fields, larger) | r |
| 1. Lagrangian | Subgradient ascent on the shortest-path Lagrangian over **all** of E on the forced blocks, as in `../capacity-lagrangian-race-v1/canzar_lagrangian.py:176-407`, with the MILP fallback (`:409` on) **disabled**. Its best potentials are exported as integers and scored by Lemma 2 (sorted charges) | the largest T + 1 with S_T < Π, exactly checked |
| 2. Defect tree | `../capacity-ladder-v1/ladder.py` as frozen (SHA-256 in its `SHA256SUMS`), `analyze(programs, 'W2', max_level=3, seconds=50)`, default limits, under the 60 s process limit. A process killed at the limit is scored at r | its `lowerBound` (search-backed allowed) for the prior and for C2; its certificate, if it exists and meets the caps, for the checkable-tree bound |
| 3. HiGHS | The flow formulation on the forced blocks (binary x_t, continuous arc flows, unit flow per block), as in `../capacity-race-v1/race_canzar.py`, via `scipy.optimize.milp` (SciPy 1.18.0 and its bundled HiGHS), minimising Σ x_t, 60 s | claimed: ceil(MIP dual bound − 10⁻⁶). Certified: the root LP dual turned into integer potentials and checked by Lemma 2 |
| 4. Hybrid | Below | its certificate's bound, if it meets the caps |

**The hybrid (arm 4).** It climbs J = 0, 1, 2, …, with T = r + J, while each level is refuted within 60 s. It also
gets arm 1's global potentials as its Lg leaf, computed inside its own 60 s.

- Branching happens only at depth 0 and depth 1 (two branching levels). At a node with an uncoverable occurrence,
  the children are the spaces Φ + ⟨φ(e)⟩ over the eligible entries e through the chosen occurrence, with E filtered
  to φ(e) ∈ Φ when testing coverability. At a node without one, the children are the wide-fallback directions,
  and an L0 leaf must first refute Φ(D) = Φ.
- Where the fan-out exceeds **q_max = 64**, or at depth 2, the node becomes a leaf, and the cheapest sound kind is
  tried in order. A *terminal stuck check* applies at spare 0, or at spare 1 when every child, at most q_max of
  them, has an uncoverable occurrence. It is checked by the lemma and never recurses. Then L0 at spare 0, L1 at
  spare 1 at a node with an uncoverable occurrence, and Lg otherwise.
- Each L0 or L1 dual gets at most 2 s of subgradient ascent. All arithmetic in the certificate is in integers.
- A level whose certificate would break a hard constraint is treated as not refuted, and the climb stops.

**Reference only, not an arm:** the frozen `canzar_lagrangian.py` with its own defaults, so it can be seen that
arm 1 is not weaker than the earlier baseline. It is checked on the seen corpora only (see the plan), not on the
new families.

**Decision runs for kill (c):** on each family where the hybrid strictly wins, HiGHS is also given the feasibility
problem with Σ x_t ≤ B − 1, where B is the hybrid's bound, for 60 s. "Solves" means it reports infeasible.

## How answers are checked

- **Independent verifier (`verify_independent.py`).** It shares **no code** with anything in this repository and
  imports only the Python standard library. It recomputes the forced cuts, the eligible set under W, the block
  rank in the certificate's prime and the kernel check (rows independent, orthogonal to every block, count
  |Σ| − r). For every tree node it checks uncoverability and the child spaces. For every leaf it recomputes P from
  E (L0, L1 or Lg), recomputes every charge from the integer potentials, and checks S_T < Π, or that some block
  has no parse by P. It also reads the `bits-defect-tree/v1` schema of `capacity-ladder-v1`, so arm 2's
  certificates are verified the same way. Its author writes it from this file and the schema only, does not read
  the hybrid's code, and is named in `RESULTS.md`.
- **Agreement.** On every `bits-defect-tree/v1` certificate, the new verifier and
  `../capacity-ladder-v1/check_certificate.py` must agree (both accept or both reject).
- **Dictionaries.** Every dictionary from any arm is replayed by the independent verifier and by the capped
  checker of `../capacity-boundary-v1/capped.py`. Only a dictionary both accept is an upper bound.
- **Exhaustive tiny-corpus audit (`audit_hybrid.py`, control).** In the style of
  `../capacity-ladder-v1/audit_ladder.py`. It uses the same generators with seeds 1 and 2, a fresh seed 3, and one
  added family, "squares", whose texts contain eligible pairs s and ss, so that parallel φ occur. Levels up to 3,
  rule W2. For each corpus: the exhaustive minimum from `../capacity-complexity-v1/evaluate.py`; the hybrid's bound
  must be at most the minimum; every certificate must be accepted by the independent verifier. On corpora with at
  most 18 eligible entries, **every L0 and L1 leaf claim is checked by brute force**: all D ⊆ E with |D| ≤ T are
  listed, and none may lie in C_T(Φ, j).
- **Positive control.** The same audit runs an *unsound* variant whose leaves use "E(Φ) plus at most k entries
  outside it". The audit must catch it at least once, as a wrong bound or a leaf refuted by brute force. If it does
  not, the audit is too weak: gadgets are added and the audit rerun before the main run, and both runs are
  reported.
- If any certified lower bound on a family exceeds a replayed dictionary there, that is a failure and work stops.

## Scoring

- Primary: |G|; shrunk and closed counts over G, with the prior both as defined (HiGHS claimed) and certified-only;
  C1 held or not. Per family: prior, which part of the prior is largest, checkable-tree bound, and best upper
  bound.
- Secondary: the number of families where arm 4 > max(arm 1, arm 2), with the leaf kinds behind each win; the
  verification-time distribution; C2 held or not; each kill condition.

## Kill thresholds for the hybrid direction

Retire the hybrid direction (not the defect tree) if **any** of these holds:

- **(a)** the hybrid strictly beats max(arm 1, arm 2) on fewer than 5 of the 40 families;
- **(b)** the median independent verification time of its non-trivial certificates exceeds 5 s;
- **(c)** HiGHS is at least 90 % faster: on the families where the hybrid strictly wins, the decision runs report
  infeasible on all of them, and their median wall time is at most one tenth of the hybrid's median wall time on
  those families (search plus certificate emission). HiGHS counts here on its claims, as O5 allows nothing else.
  A hybrid whose remaining value would be its certificate alone needs its own claim;
- **(d)** any wrong bound, or any leaf refuted by brute force, for the sound hybrid in the audit.

Between C2 and the kill thresholds (for example 5 to 7 wins, or a median of 2 to 5 s) the claim is **not
supported but not retired**. One follow-up registration on new data is allowed then. Nothing is retuned on these
40 families.

## Predictions

| | Prediction | Passes when |
| --- | --- | --- |
| P1 | No contradiction: no certified bound exceeds a replayed dictionary. The new verifier and `check_certificate.py` agree on every `bits-defect-tree/v1` certificate | zero contradictions and zero disagreements (gate: work stops otherwise) |
| P2 | The strongest prior bound leaves a gap on few families | 3 ≤ \|G\| ≤ 10 |
| P3 | Checkable trees shrink most gaps | shrunk ≥ ⌈\|G\| / 2⌉ |
| P4 | Checkable trees rarely close a gap exactly: C1 fails | closed ≤ 1 |
| P5 | The hard caps rarely bind | at most 2 of 40 families lose a certificate to a cap alone |
| P6 | The hybrid's strict wins are few: kill (a) fires | strict wins ≤ 4 |
| P7 | Where the hybrid wins, an L0 or L1 leaf does it at a node where arm 2 stalled in a fixed-space search | at least half of the strict wins (scored vacuous if there are none) |
| P8 | Hybrid certificates are quick to check | median ≤ 2 s and maximum ≤ 30 s over its non-trivial certificates |
| P9 | HiGHS does not dominate at this size | arm 3 reports optimality within 60 s on at most 20 of 40, and kill (c) does not fire |
| P10 | The audit finds the sound hybrid sound and catches the unsound control | ≥ 10,000 comparisons, zero wrong bounds or refuted leaves for the sound variant, at least one catch for the unsound one |

Scoring is as in `../capacity-deficit-race-v1/RESULTS.md:58-72`: each prediction **held** or **wrong**, stated with
its count, with no partial credit and no rewording after the run.

P4 and P6 are forecasts that the claims fail. They follow from what is known below and from the r + 4 ceiling
derived above. The run is still worth its $0. It measures whether trees close anything the full prior leaves open
on unseen code, it gives every refutation above the prior a checkable certificate under fixed caps, and it tests
the L0 leaf at exactly the point where the ladder's fixed-space search stalls (`../capacity-ladder-v1/RESULTS.md:25-27`).

## What was known when this was written

- **A08** (three, 6 files): the tree proves 71 with 12 nodes, checked in 2 s, and a 72-entry dictionary replays
  (`../capacity-ladder-v1/RESULTS.md:48`, `real-corpora.json:1731-1738`). The Lagrangian baseline stops at 69
  (`../capacity-deficit-race-v1/RESULTS.md:19`, `:30-31`; `measurements-a.json:263-264`).
- **race/B04** (twin WGSL shader pairs): the tree stops at 25 with 86 nodes
  (`../capacity-ladder-v1/real-corpora.json:782-785`). Level 3 was undecided because "1512 branches at one
  occurrence exceed the limit" (`real-corpora.json:797`; `RESULTS.md:50`, `:53-55`). The best stored lower bound
  is 30. It is **not** a Lagrangian or LP dual value: it is the shipped diagnostic's disjoint-position bound
  (`../capacity-race-v1/race-results.json:404-408`). The HiGHS flow LP timed out at 60 s
  (`../capacity-race-v1/RESULTS-RACE.md:45-46`), and no Lagrangian run on B04 is stored.
  `../capacity-ladder-v1/RESULTS.md:50` and `:55` call that 30 the baseline's linear-program bound. A
  disjoint-position witness is a feasible point of the dual of the position-covering relaxation, not a computed
  LP optimum.
- **PY-3**: the tree proves 55 with 4,141 nodes (`../capacity-ladder-v1/RESULTS.md:49`, `real-corpora.json:254-257`),
  stored compressed at 8.9 MB. Its own docstring puts a deep verification at "about a quarter of an hour"
  (`verify_stored.py:9`, `:14`). No measured verification time is stored in the repository.
- **Earlier families.** In set A of `capacity-deficit-race-v1`, 8 of 24 families were non-saturated, and levels
  0 and 1 settled 7 of those 8 (`RESULTS.md:13-25`). On the 59 corpora of `capacity-ladder-v1`, 56 are settled,
  3 are open, and the ladder tightened all 3 but closed none (`RESULTS.md:34-56`). On B04 the tightened bound is
  still below the prior.
- Exhaustive audit of the ladder: 13,796 checks with no wrong bound, and 367 certificates accepted
  (`../capacity-ladder-v1/RESULTS.md:11-24`).
- None of the 15 sources above has been opened for this work.

## What would change our mind

- **Toward the trees:** closed ≥ ⌈|G| / 3⌉ with |G| ≥ 3 under the caps. Checkable trees would then be a routine tool
  past the prior on unseen code, not a curiosity of three corpora.
- **Toward the hybrid:** ≥ 8 strict wins at a median verification time of at most 2 s. Or a sound answer to O1,
  which removes the r + 4 ceiling and would deserve its own registration.
- **Against both:** |G| < 3, which would mean that block rank, level 0/1 and the duals settle unseen families on
  their own. Or HiGHS settling, on its claims, every gap the trees shrink, which would leave the trees' value
  only in the certificate.
- **Against the method of proof:** any wrong bound in the audit or on the corpus. That stops this work and reopens
  the lemmas above.

## Implementation plan (NOT YET BUILT)

None of these files exists. Each is written after this file is committed and before `SHA256SUMS-CODE` is
committed, and is tried only on the 59 seen corpora of `capacity-ladder-v1` and on the audit corpora.

| File | Purpose |
| --- | --- |
| `select_instances.py` | The selection rule above; writes `instances.json`, `selection-log.json`, `source-pins.json`; no local paths in outputs |
| `hybrid.py` | Arms 1 and 4. Shares one dual routine (subgradient → integer potentials → Lemma 2 test) between them. Writes schema `bits-hybrid-certificate/v1` (kernel, prime, base, T, nodes with spare, leaves with kind and potentials) |
| `highs_arm.py` | Arm 3 and the kill-(c) decision runs; exports root-LP potentials in the same integer form |
| `verify_independent.py` | The zero-shared-code verifier for both schemas, plus dictionary replay; standard library only |
| `audit_hybrid.py` | The exhaustive audit, the leaf brute force and the unsound positive control |
| `run.py` | One process per family per arm, limits, affinity and CPU-time recording; writes `measurements.json` |
| `score.py` | Rebuilds every count in "Scoring" from `measurements.json`, the certificates and the verifier; writes `results.json` |

Checks before the main run, all on seen data: arm 1 ≥ 69 on A08; arm 2 reproduces the stored 71 and 25 on A08 and
B04; arm 1 ≥ the frozen baseline on the 59 seen corpora; the hybrid is ≥ arm 2 on every seen corpus where arm 2's
certificate meets the caps; the verifier accepts the six stored ladder certificates and rejects the four tampered
copies of `../capacity-ladder-v1/verify_stored.py:74-99`; P10's audit passes.

## Order of events

1. Commit this file and `README.md` (draft).
2. Settle O5, and record the answer here as a dated amendment before step 3.
3. Run `select_instances.py` once and commit its outputs with `SHA256SUMS-CORPUS`. The registration binds here.
4. Build and test the code on seen data only, then commit `SHA256SUMS-CODE`.
5. Run every arm on the 40 families, then the audit, then score. Write `RESULTS.md` with every deviation listed.

Any change to arms, limits, caps, thresholds or predictions after step 3 is a deviation and is reported as one.
