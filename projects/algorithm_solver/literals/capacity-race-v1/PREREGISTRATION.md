# Pre-registration: Structural Nullspace-Kernel Theorem and Head-to-Head Race vs. Canzar et al. (2012) Near 64 Slots

Frozen **before** running either BITS or Canzar et al.'s flow solver on any corpus in `boundary-instances.json`.

## 1. Structural Theorem (The Forced-Block Nullspace-Kernel Theorem)

Under witness rule $W_k$ ($k \ge 2$, whole programs excluded, token UTF-8 byte cap $160$), no eligible token can cross a forced cut (an adjacent bigram occurring in fewer than $k$ programs). Let $B = \mathrm{forced\_blocks}(P, k)$ be the set of distinct mandatory blocks and let $M_B$ be its position-weighted character incidence matrix over each prime field $(\mathbb{F}_p, \beta)$ attaining maximum rank $r = \max_p \mathrm{rank}_{\mathbb{F}_p}(M_B) = |\Sigma| - d$, where $d = |\Sigma| - r$ is the **nullity (rank defect)**.

Define:
- **Nullspace support** $S_{\mathrm{free}} = \bigcup_{\text{attaining } p} \mathrm{supp}(\ker_{\mathbb{F}_p}(M_B))$ (the characters whose unit vectors $e_c$ do not lie in $\mathrm{rowspace}(M_B)$ in every attaining field).
- **Determined alphabet** $S_{\mathrm{det}} = \Sigma \setminus S_{\mathrm{free}}$, and kernel budget $k_{\mathrm{free}} = |S_{\mathrm{free}}| - d$.
- **Nullspace-orthogonal eligible fragments** $E_{\mathrm{span}}^{\mathrm{free}} = \{t \in E_k : K_p \cdot v_p(t) = 0 \text{ in every attaining field},\; \mathrm{chars}(t) \cap S_{\mathrm{free}} \neq \emptyset\}$.
- **Forced $D_{\mathrm{det}}$-segments** $B_{\mathrm{det}}^{\star}$: maximal contiguous substrings of blocks in $B$ not covered by any occurrence of $E_{\mathrm{span}}^{\mathrm{free}}$ whose left and right boundaries are each either a block edge or a character in $S_{\mathrm{free}}$. Let $r_{\mathrm{det}}^{\star} = \max_p \mathrm{rank}_{\mathbb{F}_p}(M_{B_{\mathrm{det}}^{\star}})$ and $\Delta_{\mathrm{det}}^{\star} = |S_{\mathrm{det}}| - r_{\mathrm{det}}^{\star}$.

**Theorem 1 (Nullspace-Kernel Characterization of Rank Attainment):**
Assume all singletons in $S_{\mathrm{det}}$ are eligible.
1. *(Sufficiency / Exact Construction)* If there exists $T \subseteq E_{\mathrm{span}}^{\mathrm{free}}$ of size $|T| \le k_{\mathrm{free}}$ such that $S_{\mathrm{det}} \cup T$ parses every forced block $b \in B_{\mathrm{free}}$ touching $S_{\mathrm{free}}$, then $D = S_{\mathrm{det}} \cup T$ is an **exact optimal dictionary** of size $r = \mathrm{OPT}_{W_k}(P)$.
2. *(Necessity / Impossibility Lift)* In any legal dictionary $D$ of size $r$, $D \subseteq E_{\mathrm{span}}$ and $D_{\mathrm{det}} = D \setminus D_{\mathrm{free}}$ must parse every segment in $B_{\mathrm{det}}^{\star}$ without crossing into $S_{\mathrm{free}}$, so $|D_{\mathrm{det}}| \ge r_{\mathrm{det}}^{\star}$ and $|D_{\mathrm{free}}| \le k_{\mathrm{free}} + \Delta_{\mathrm{det}}^{\star}$. Replacing every token of $D_{\mathrm{det}}$ by singletons in $S_{\mathrm{det}}$ preserves parsing of $B_{\mathrm{free}}$. Therefore, if no $T \subseteq E_{\mathrm{span}}^{\mathrm{free}}$ of size $\le k_{\mathrm{free}} + \Delta_{\mathrm{det}}^{\star}$ parses $B_{\mathrm{free}}$ alongside $S_{\mathrm{det}}$, then $\mathrm{OPT}_{W_k}(P) \ge r + 1$.
3. *(Defined Exact Class)* Whenever $\Delta_{\mathrm{det}}^{\star} = 0$ and $d \in \{0, 1\}$, exact capacity $\mathrm{OPT}_{W_k}(P) \in \{|\Sigma|-d, |\Sigma|\}$ is decided purely by this kernel check (polynomial for bounded $|S_{\mathrm{free}}|$). For any $d \ge 1$ with $\Delta_{\mathrm{det}}^{\star} = 0$, exact rank attainment ($\mathrm{OPT}_{W_k}(P) = r$) is equivalent to a size-$k_{\mathrm{free}}$ cover of $B_{\mathrm{free}}$ in $E_{\mathrm{span}}^{\mathrm{free}}$.
4. *(Failure Boundaries)* The kernel check alone can remain `UNRESOLVED` when (a) $d \ge 2$ and $\mathrm{OPT}_{W_k}(P) \ge r + 2$ (as in Néraud's vertex-cover graphs $K_4$, $K_5$, prism), (b) $\Delta_{\mathrm{det}}^{\star} > 0$, or (c) $|S_{\mathrm{free}}|$ is large.

## 2. Unseen Evaluation Set & Symmetric Race Rules

- **Corpora:** `12` mutually disjoint unseen source-code projects (`B01`..`B12`, spanning Python, Zig, WGSL, JavaScript, and C; $|\Sigma| \in [58, 74]$, 8 strictly in $[64, 71]$), selected by isolated read-only subagent `a7d22714-d5ae-4c23-8949-8780036cd6e6` (zero reads of `projects/algorithm_solver/`).
- **Queries (`24` total):** Under `W2` (`max_bytes = 160`, whole-program excluded), every corpus is queried at:
  1. `K = 64` (the primary 6-bit boundary), and
  2. `K = |Sigma| - 2` (or `|Sigma| - 1` when `|Sigma| < 64`), stressing below-alphabet construction vs. impossibility.
- **Competitors (identical preprocessing & identical verification bar):**
  - **BITS (`diagnostic.py`):** pure Python stdlib (`forced_blocks` rank + forced-block components + Nullspace-Kernel Theorem + fast disjoint packing + fast constructive dictionary pass). Zero LP/MILP solver.
  - **Canzar et al. (2012) Flow Solver (`scipy.optimize` HiGHS):** strongest fair implementation on the **same** deduplicated `forced_blocks` and trivial $|\Sigma| \le K$ singleton check: (1) HiGHS **primal flow LP** + exact `Fraction` dual potential verification (`ceil(val) > K` -> `IMPOSSIBLE`) + LP-integral dictionary check, falling back to (2) HiGHS **flow MILP** with byte-exact parse verification.
- **Same verified artifact bar:**
  - `IMPOSSIBLE`: independently verified lower-bound certificate proving $\mathrm{OPT} > K$ (no floating-point trust).
  - `FEASIBLE`: independently verified legal dictionary $D$ ($|D| \le K$) with every entry checked eligible under `W2` and every source byte reconstructed identically.
  - `UNRESOLVED` / `TIMEOUT`: counted explicitly; per-query wall-clock limit `60.0 s`.
- **Timing & memory:** Pure wall-clock timing (`measure_memory=False`, zero `tracemalloc` overhead) for both methods on identical hardware; peak Python traced allocation measured in a separate pass.

## 3. Pre-registered Predictions (Frozen Before Scoring)

- **P1 (Zero soundness violations — hard gate):** `0` verdict contradictions (`IMPOSSIBLE` vs. `FEASIBLE`) between BITS and Canzar across all `24` queries; 100% of returned `IMPOSSIBLE` certificates and `FEASIBLE` dictionaries pass independent verification.
- **P2 (Nullspace-kernel structure on unseen code):** At least `8/12` unseen corpora satisfy $\Delta_{\mathrm{det}}^{\star} = 0$ with $|S_{\mathrm{free}}| \le 12$, and at least `2/12` unseen corpora achieve $\mathrm{OPT}_{W_2} < |\Sigma|$ via shared multi-character fragments (showing `C-1`/`C-2` are not isolated flukes).
- **P3 (Rejection speed — `IMPOSSIBLE` queries):** On non-trivial `IMPOSSIBLE` queries ($K < |\Sigma|$), BITS settles at least `90%` of the queries Canzar settles with a median wall-clock speedup of at least `10x` over Canzar's primal flow LP.
- **P4 (Below-alphabet construction — `FEASIBLE` queries with $K < |\Sigma|$):** Whenever an unseen corpus has $\mathrm{OPT}_{W_2} \le K < |\Sigma|$ and $\mathrm{OPT}_{W_2} = r$ with $\Delta_{\mathrm{det}}^{\star} = 0$, the Nullspace-Kernel Theorem certifies `FEASIBLE` faster than Canzar (`>= 5x` median speedup). **Narrowing rule:** if BITS only wins on rejections (`IMPOSSIBLE`) and misses or loses on below-alphabet `FEASIBLE` queries, we narrow the claim to rejection certification only.
- **P5 (Unresolved honesty):** Any query with $d \ge 2$ and $\mathrm{OPT} \ge r + 2$ (or large $|S_{\mathrm{free}}|$) may remain `UNRESOLVED` for BITS and is reported verbatim alongside timeouts without redefining the protocol.
