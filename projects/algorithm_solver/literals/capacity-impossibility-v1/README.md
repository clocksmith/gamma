# Disjoint-Position Capacity Impossibility Bound & Scale-1 Dual Shortcut (`capacity-impossibility-v1`)

Pinned source commit: [`clocksmith/gamma@59ff04415ff2afd04ff2ed451340f4f02852bf18`](https://github.com/clocksmith/gamma/tree/59ff04415ff2afd04ff2ed451340f4f02852bf18/projects/algorithm_solver/literals)

This directory extends the `matched80` 74-singleton check to a general, solver-free combinatorial lower bound across witness thresholds $k \ge 1$ and frozen JavaScript, Python, and C corpora, without altering or delaying the frozen `sixbit-v1` compact-corpus artifacts.

## 1. Theorem, Scale-1 Dual Embedding, and Alphabet-Saturation Shortcut

For a corpus $\mathcal{T} = \{T_1, \dots, T_N\}$ with alphabet $\Sigma = (\bigcup_p \text{chars}(T_p)) \setminus \mathcal{W}_{\text{whole}}$ and witness threshold $k \ge 1$, let $\mathcal{E}_k(\mathcal{T})$ be the eligible token set:
- **$k = 1$ (rule $U$):** every non-empty substring occurring in $\mathcal{T}$ that is not equal to a whole program in $\mathcal{T}$.
- **$k \ge 2$ (rule $W_k$):** every single character in $\Sigma$, plus every non-whole substring of length $\ge 2$ and UTF-8 byte length $\le 160$ occurring in at least $k$ distinct programs of $\mathcal{T}$.

For each character position $u = (p, i)$ ($0 \le i < |T_p|$), define its **eligible cover set**
$$C_k(p, i) = \{\, T_p[a:b] \in \mathcal{E}_k(\mathcal{T}) \mid 0 \le a \le i < b \le |T_p| \,\}.$$
Any dictionary $D \subseteq \mathcal{E}_k(\mathcal{T})$ that tiles every $T_p \in \mathcal{T}$ must hit $C_k(p, i)$ at every position $(p, i)$.

1. **Disjoint-position lower bound ($B_{\text{disj}}(k)$):** Let $F_1(k) = \{ c \in \Sigma : \exists u_c \text{ with } C_k(u_c) = \{c\} \}$ be the forced singleton set, and let $M(k)$ be any set of residual positions ($T_p[i] \notin F_1(k)$) whose cover sets $C_k(u)$ are non-empty and pairwise disjoint. Because $F_1(k)$ contains only length-1 tokens and $T_p[i] \notin F_1(k)$ for $u \in M(k)$, the $|F_1(k)| + |M(k)|$ sets $\{C_k(u_c)\}_{c \in F_1(k)} \cup \{C_k(u)\}_{u \in M(k)}$ are pairwise disjoint, forcing
   $$|F_1(k)| \le B_{\text{disj}}(k) := |F_1(k)| + |M(k)| \le \text{OPT}_A(k) \le |\Sigma|.$$
2. **The `scale = 1` step potential, and when its dual equals the bound:** For any disjoint witness $W = \{ (p_1, i_1), \dots, (p_m, i_m) \}$, define integer step potentials at `scale = 1` by
   $$\pi_{p, j} = |\{ r \in \{1, \dots, m\} : p_r = p \text{ and } i_r \ge j \}|.$$
   Each occurrence $T_p[a:b]$ of $s \in \mathcal{E}_k(\mathcal{T})$ has $\pi_{p,a} - \pi_{p,b} = |\{ r : p_r = p,\; a \le i_r < b \}|$. The Experiment A dual sums over **every occurrence** of $s$, so the rebate of $s$ is the number of pairs (occurrence, witness position) in which the occurrence spans the position. Pairwise disjointness limits $s$ to one witness position. It does not limit $s$ to one occurrence there: a token that overlaps itself can span the same position twice. In `aaa` under $U$, `aa` starts at 0 and at 1 and both occurrences span position 1, so its rebate is 2, and $L_A(\pi_W) = 0$ while $B_{\text{disj}} = 1$. In general
   $$L_A(\pi_W) = |W| - \sum_{s} \max\!\big(0,\ \text{rebate}_s - 1\big) \;\le\; B_{\text{disj}}(k),$$
   with equality **exactly when no eligible token is charged twice**. The bound in item 1 does not depend on this: it is combinatorial and always sound. A dual that took the maximum over the occurrences spanning each cut would give the equality in general. That is a different formulation, and it is not what this verifier evaluates.
3. **Alphabet-saturation shortcut:** Because the single-character dictionary $D = \Sigma$ always tiles every program (when $\Sigma$ contains all characters of $\mathcal{T}$), $|\Sigma|$ is a feasible upper bound on $\text{OPT}_A(k)$. Whenever $B_{\text{disj}}(k) = |\Sigma|$, the lower bound meets the single-character upper bound:
   $$B_{\text{disj}}(k) = \text{OPT}_A(k) = |\Sigma| \quad (\text{gap} = 0),$$
   with zero LP or MILP solver calls. This uses item 1 only. The step potential is in addition an exact `scale = 1` dual certificate, $L_A(\pi_W) = |\Sigma|$, when no token is charged twice. Each row of `results.json` records `all_occurrences_dual`, `tokens_counted_twice` and `dual_equals_disjoint_bound`; on all 42 rows below no token is charged twice.
4. **Impossibility test, not a sufficiency criterion:** Covering every position individually does not guarantee non-overlapping tiling. On $\mathcal{T} = \{\text{"abcd"}, \text{"abce"}, \text{"fbcd"}\}$ at $k = 2$ ($|\Sigma| = 6$), the 4-token set $\{\text{"abc"}, \text{"bcd"}, \text{"e"}, \text{"f"}\}$ covers every position of all three strings ($B_{\text{disj}}(2) = 4$), yet `"abc"` and `"bcd"` overlap on `"bc"` rather than tiling `"abcd"`; exact tiling requires $5$ entries, certified by the path-flow Lagrangian dual $\lceil L_A(\pi^*) \rceil = 5$ (`overlapping_non_tiling_counterexample()`).

## 2. Six-Corpus Receipt (`results.json` & `certificates.json`, Independently Replayed)

All 42 `(corpus, k)` rows below are replayed from frozen Git blobs at `59ff0441` without invoking any solver (`replay_verify_receipt.py`). For each row the replay checks that the witness positions have pairwise disjoint cover sets, then evaluates the all-occurrences dual of the step potential, counting every eligible occurrence that spans a witness position. On all 42 rows the witness is disjoint and the dual equals the disjoint bound.

| Corpus (`N`, bytes) | Threshold / Rule | $\|\Sigma\|$ | Forced singletons $\|F_1\|$ | Disjoint bound $B_{\text{disj}}$ | Certified lower bound | Feasible upper bound | Remaining gap | Shortcut ($B_{\text{disj}} = \|\Sigma\|$) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| **`js_matched80_compact`** (`80`, 18,542 B) | `k = 1` (`U`) | 92 | 0 | 46 | **79** (`59ff0441` LP dual) | **79** | **0** | no |
| | `k = 2` (`W`) | 92 | 74 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 3` (`W`) | 92 | 89 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 4` (`W`) | 92 | 91 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 5` (`W`) | 92 | 91 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 8` (`W`) | 92 | 91 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 10` (`W`) | 92 | 91 | **92** | **92** | **92** | **0** | **yes** |
| **`js_matched80_canonical`** (`80`, 40,467 B) | `k = 1` (`U`) | 92 | 0 | 47 | 47 (disjoint witness) | 79 (stored cover, replayed here) | 32 | no |
| | `k = 2` (`W`) | 92 | 68 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 3` (`W`) | 92 | 73 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 4` (`W`) | 92 | 77 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 5` (`W`) | 92 | 77 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 8` (`W`) | 92 | 79 | **92** | **92** | **92** | **0** | **yes** |
| | `k = 10` (`W`) | 92 | 82 | **92** | **92** | **92** | **0** | **yes** |
| **`js_sub12_compact`** (`12`, 2,691 B) | `k = 1` (`U`) | 66 | 0 | 12 | 12 | 66 | 54 | no |
| | `k = 2` (`W`) | 66 | 51 | **66** | **66** | **66** | **0** | **yes** |
| | `k = 3` (`W`) | 66 | 60 | **66** | **66** | **66** | **0** | **yes** |
| | `k = 4` (`W`) | 66 | 61 | **66** | **66** | **66** | **0** | **yes** |
| | `k = 5` (`W`) | 66 | 61 | **66** | **66** | **66** | **0** | **yes** |
| | `k = 8` (`W`) | 66 | 63 | **66** | **66** | **66** | **0** | **yes** |
| | `k = 10` (`W`) | 66 | 64 | **66** | **66** | **66** | **0** | **yes** |
| **`py_paired80_fit`** (`80` Python, 56,289 B) | `k = 1` (`U`) | 83 | 0 | 64 | 64 | 83 | 19 | no |
| | `k = 2` (`W`) | 83 | 45 | **83** | **83** | **83** | **0** | **yes** |
| | `k = 3` (`W`) | 83 | 57 | **83** | **83** | **83** | **0** | **yes** |
| | `k = 4` (`W`) | 83 | 63 | **83** | **83** | **83** | **0** | **yes** |
| | `k = 5` (`W`) | 83 | 64 | **83** | **83** | **83** | **0** | **yes** |
| | `k = 8` (`W`) | 83 | 70 | **83** | **83** | **83** | **0** | **yes** |
| | `k = 10` (`W`) | 83 | 75 | **83** | **83** | **83** | **0** | **yes** |
| **`py_devval100_readable`** (`100` Python, 44,065 B) | `k = 1` (`U`) | 71 | 0 | 59 | 59 | 71 | 12 | no |
| | `k = 2` (`W`) | 71 | 28 | **71** | **71** | **71** | **0** | **yes** |
| | `k = 3` (`W`) | 71 | 41 | **71** | **71** | **71** | **0** | **yes** |
| | `k = 4` (`W`) | 71 | 52 | **71** | **71** | **71** | **0** | **yes** |
| | `k = 5` (`W`) | 71 | 55 | **71** | **71** | **71** | **0** | **yes** |
| | `k = 8` (`W`) | 71 | 63 | **71** | **71** | **71** | **0** | **yes** |
| | `k = 10` (`W`) | 71 | 64 | **71** | **71** | **71** | **0** | **yes** |
| **`c_tools_33`** (`33` C files $\le 8\text{ KB}$, 138,559 B) | `k = 1` (`U`) | 91 | 0 | 30 | 30 | 91 | 61 | no |
| | `k = 2` (`W`) | 91 | 49 | **90** | **90** | 91 | **1** | no (`90 > 64` still rules out 6-bit) |
| | `k = 3` (`W`) | 91 | 62 | **91** | **91** | **91** | **0** | **yes** |
| | `k = 4` (`W`) | 91 | 72 | **91** | **91** | **91** | **0** | **yes** |
| | `k = 5` (`W`) | 91 | 73 | **91** | **91** | **91** | **0** | **yes** |
| | `k = 8` (`W`) | 91 | 80 | **91** | **91** | **91** | **0** | **yes** |
| | `k = 10` (`W`) | 91 | 83 | **91** | **91** | **91** | **0** | **yes** |

**Canonical $U$ is reported in two separate lanes.** The disjoint witness of this folder gives 47, and that is the number in the table. The exact value is 79: the 80 canonical program vectors have rank 79 over a prime field, and a stored 79-entry dictionary rebuilds all 80 programs byte for byte (the rank proof tracked in clocksmith/deco#203). That result comes from a different argument, is not checked by this folder's replay, and is not folded into the 47 row. Entry-count results such as these are also kept apart from the escape-cost certificates in `sixbit-v1`.

**Regressions.** `test_impossibility_bound.py` keeps two cases where the disjoint bound holds and the dual equality fails: `aaa` under $U$, and `aaa` with `aab` under $W_2$. In both, `aa` spans position 1 of `aaa` twice. The tests also compare the verifier's dual with a direct evaluation from the definition, and check that a witness whose cover sets share a token is rejected.

## 3. Reproduce and Independently Replay

```sh
# 1. Unit tests (non-tiling counterexample, scale-1 dual and its two self-overlap regressions, tiny brute-force oracles, negative tests)
python3 -B -m unittest discover -s projects/algorithm_solver/literals/capacity-impossibility-v1 -v

# 2. Standalone solver-free certificate replay from pinned Git blobs at 59ff0441
python3 -B projects/algorithm_solver/literals/capacity-impossibility-v1/replay_verify_receipt.py
```
