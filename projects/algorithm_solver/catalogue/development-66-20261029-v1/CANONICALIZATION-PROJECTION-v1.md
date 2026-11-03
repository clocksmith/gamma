# Canonicalization Projection Study (Task 1.2)

- **Schema:** `gamma.development-canonicalization-projection.v1`
- **Qualification:** `unknown` (development-only projection; no catalogue admissions or qualification states changed)
- **Receipt:** [`runs/canonicalization-9-20261102/results.json`](runs/canonicalization-9-20261102/results.json)
- **Runner:** [`measure_canonicalization.py`](measure_canonicalization.py)
- **Unit & Contract Tests:** [`test_canonicalization.py`](test_canonicalization.py)

## 1. Sample Selection and Invariants

Nine problems from the 66-problem development cohorts (`requested-243-370-35-20261028-v1` and `requested-156-1940-31-20261028-v1`) were evaluated across both Python and JavaScript (`9 problems x 2 languages x 3 variants = 54 module variants`):

1. **Five Revised Problems (`revised_5`):**
   - `156` (`binary-tree-upside-down`, `requested-156-1940-31-20261028-v1`) — `TreeNode` pure deep-copy `solve` (`O(n)` time/space, cycle-rejecting) + mutating native `upsideDownBinaryTree`
   - `280` (`wiggle-sort`, `requested-156-1940-31-20261028-v1`) — pure `solve` + `in_place_arg: 0` void `wiggleSort` under `wiggle_sort` valid-output comparator
   - `286` (`walls-and-gates`, `requested-156-1940-31-20261028-v1`) — pure `solve` + `in_place_arg: 0` row-mutating void `wallsAndGates`
   - `340` (`longest-substring-with-at-most-k-distinct-characters`, `requested-243-370-35-20261028-v1`) — `string_unit: unicode_codepoint` (`Array.from(s)` in JS) with non-BMP canary coverage
   - `903` (`valid-permutations-for-di-sequence`, `requested-156-1940-31-20261028-v1`) — `string_unit: ascii` dynamic programming with module-level `MOD` constant
2. **Four Untouched Controls (`control_4`):**
   - `250` (`count-univalue-subtrees`, `requested-243-370-35-20261028-v1`) — `TreeNode` recursive DFS with `nonlocal cnt` / closure state
   - `270` (`closest-binary-search-tree-value`, `requested-243-370-35-20261028-v1`) — `TreeNode` iterative BST walk with float target tie-breaking
   - `737` (`sentence-similarity-ii`, `requested-156-1940-31-20261028-v1`) — nested `find` disjoint-set union with generator/comprehension query check
   - `1214` (`two-sum-bsts`, `requested-156-1940-31-20261028-v1`) — two-tree iterative traversal with helper `_collect` / `collect`

### Three Variants Compared

- **`raw`**: Exact receipt-bound source bytes on disk in `catalogue/authored/`. Zero bytes in `catalogue/authored/` were modified (`authored_files_untouched: true`, verified by pre/post SHA256 check).
- **`formatted`**: Deterministic AST-normalized formatting (`ast.unparse` in Python after stripping module/function docstrings; `escodegen` 2-space canonical ESTree formatting in JavaScript after `acorn.parse`), preserving all original identifier names, type annotations, `'use strict'`, helpers, and native/pure exports. Verified for AST and binding-fingerprint equivalence.
- **`compact_palette`**: AST-aware capture-safe local binding renaming to the positional palette (`a, b, c, ...`) via conflict-graph coloring over lexical scopes (`PyBindings` in Python; `eslint-scope` `bindings.mjs` in JavaScript), plus compact token emission (1-space indentation in Python, minimal lexical separator spacing in both languages). Module-level exports (`solve`, `<nativeMethod>`, `Solution`, `TreeNode`, `MOD`) and property accesses (`.val`, `.left`, `.right`, `.exports`) remain untouched. Verified by re-parsing the emitted compact source and asserting exact binding-graph fingerprint equivalence (`binding_fingerprint_verified: true`) before running all execution and native ABI checks in a temporary directory.

---

## 2. Aggregate Projection Results

### 2.1 Byte, Token, and Compressibility Summary (`all_9`, `revised_5`, `control_4`)

| Language | Subgroup | `raw` Bytes | `formatted` Bytes | `compact_palette` Bytes | `raw -> formatted` | `formatted -> compact` | `raw -> compact` | `zlib-9` (`raw / fmt / cmp`) | `lzma` (`raw / fmt / cmp`) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Python | `all_9` (9) | 10,216 | 8,374 | 5,134 | -1,842 B (-18.03%) | -3,240 B (-38.69%) | -5,082 B (-49.75%) | 2,671 / 2,018 / 1,557 | 2,708 / 2,076 / 1,632 |
| Python | `revised_5` (5) | 6,328 | 4,744 | 2,978 | -1,584 B (-25.03%) | -1,766 B (-37.23%) | -3,350 B (-52.94%) | 2,052 / 1,429 / 1,143 | 2,116 / 1,504 / 1,232 |
| Python | `control_4` (4) | 3,888 | 3,630 | 2,156 | -258 B (-6.64%) | -1,474 B (-40.61%) | -1,732 B (-44.55%) | 1,006 / 935 / 701 | 1,092 / 1,024 / 800 |
| JavaScript | `all_9` (9) | 11,762 | 10,629 | 6,751 | -1,133 B (-9.63%) | -3,878 B (-36.49%) | -5,011 B (-42.60%) | 2,992 / 2,381 / 1,781 | 2,972 / 2,388 / 1,820 |
| JavaScript | `revised_5` (5) | 7,425 | 6,211 | 3,977 | -1,214 B (-16.35%) | -2,234 B (-35.97%) | -3,448 B (-46.44%) | 2,325 / 1,714 / 1,298 | 2,356 / 1,764 / 1,372 |
| JavaScript | `control_4` (4) | 4,337 | 4,418 | 2,774 | +81 B (+1.87%) | -1,644 B (-37.21%) | -1,563 B (-36.04%) | 1,075 / 1,086 / 813 | 1,144 / 1,152 / 892 |
| Combined (Py+JS) | `all_9` (18) | 21,978 | 19,003 | 11,885 | -2,975 B (-13.54%) | -7,118 B (-37.46%) | -10,093 B (-45.92%) | 5,663 / 4,399 / 3,338 | 5,680 / 4,464 / 3,452 |

### 2.2 Cross-Problem Vocabulary Concentration and Token Trigram Reuse (`all_9`)

| Language | Variant | Lexical Tokens | Identifier Occurrences | Distinct Identifiers (Union) | Top-8 Identifier Share | Top-16 Identifier Share | Distinct Token 3-Grams | Cross-Problem Shared 3-Gram Share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Python | `raw` | 2,049 | 755 | 110 | 32.32% | 46.62% | 1,148 | 45.99% |
| Python | `formatted` | 2,044 | 755 | 110 | 32.32% | 46.62% | 1,132 | 46.89% |
| Python | `compact_palette` | 1,998 | 732 | 56 | 69.40% | 83.47% | 982 | 57.07% |
| JavaScript | `raw` | 3,033 | 987 | 111 | 35.87% | 54.91% | 1,332 | 59.47% |
| JavaScript | `formatted` | 3,011 | 987 | 111 | 35.87% | 54.91% | 1,325 | 59.34% |
| JavaScript | `compact_palette` | 3,011 | 987 | 61 | 70.01% | 83.59% | 1,071 | 72.87% |

Key observations from the decomposed steps:
1. **Trivia normalization (`raw -> formatted`) vs. structural/lexical canonicalization (`formatted -> compact_palette`):**
   - `raw -> formatted` is larger on `revised_5` (`-25.03%` Python, `-16.35%` JS) than on `control_4` (`-6.64%` Python, `+1.87%` JS) because the 5 revised modules document their native effect and string-unit contracts in docstrings/comments (`156`, `280`, `286`, `340`), whereas the 4 controls only carry the 1-line header docstring in Python and no prose comments in JS (and `escodegen` expands single-line `if (...) return ...;` guards to 2-space blocks).
   - Once trivia is removed, `formatted -> compact_palette` delivers a uniform `-35.97%` to `-40.61%` byte reduction across both `revised_5` and `control_4` in both languages (`-38.69%` Python, `-36.49%` JS).
2. **Cross-problem literal & identifier sharing:**
   - Renaming local bindings per lexical scope to the conflict-free positional palette (`a, b, c, ...`) cuts the union of distinct identifiers across the 9 problems nearly in half (`110 -> 56` in Python, `111 -> 61` in JS) and doubles the share of identifier occurrences covered by the top 8 names (`32.32% -> 69.40%` in Python; `35.87% -> 70.01%` in JS).
   - As a direct consequence of local variables aligning onto `a, b, c, d`, the share of token 3-gram occurrences that are shared across at least two problems rises from `46.89% -> 57.07%` in Python and from `59.34% -> 72.87%` in JavaScript, reducing `zlib-9` compressed corpus bytes by an additional `-22.84%` beyond `formatted` in Python (`2,018 -> 1,557 B`) and `-25.20%` beyond `formatted` in JavaScript (`2,381 -> 1,781 B`).

---

## 3. Per-Problem Breakdown (54 Module Variants)

| ID | Group | Official Entry | Lang | `raw` B | `fmt` B | `cmp` B | `raw->fmt` | `fmt->cmp` | `raw->cmp` | Renamed / Eligible | Pure Cases | Native ABI Checks |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 156 | revised | `upsideDownBinaryTree` | py | 3,327 | 2,436 | 1,567 | -26.78% | -35.67% | -52.90% | 32 / 32 | 4 / 4 | 43 / 43 |
| 156 | revised | `upsideDownBinaryTree` | js | 3,587 | 2,808 | 1,829 | -21.72% | -34.86% | -49.01% | 28 / 28 | 4 / 4 | 43 / 43 |
| 280 | revised | `wiggleSort` | py | 642 | 352 | 234 | -45.17% | -33.52% | -63.55% | 6 / 6 | 4 / 4 | 53 / 53 |
| 280 | revised | `wiggleSort` | js | 800 | 579 | 397 | -27.62% | -31.43% | -50.38% | 7 / 7 | 4 / 4 | 53 / 53 |
| 286 | revised | `wallsAndGates` | py | 1,037 | 760 | 501 | -26.71% | -34.08% | -51.69% | 17 / 18 | 3 / 3 | 39 / 39 |
| 286 | revised | `wallsAndGates` | js | 1,236 | 1,156 | 675 | -6.47% | -41.61% | -45.39% | 21 / 22 | 3 / 3 | 39 / 39 |
| 340 | revised | `lengthOfLongestSubstringKDistinct` | py | 649 | 585 | 332 | -9.86% | -43.25% | -48.84% | 11 / 11 | 8 / 8 | 81 / 81 |
| 340 | revised | `lengthOfLongestSubstringKDistinct` | js | 959 | 825 | 547 | -13.97% | -33.70% | -42.96% | 12 / 12 | 8 / 8 | 81 / 81 |
| 903 | revised | `numPermsDISequence` | py | 673 | 611 | 344 | -9.21% | -43.70% | -48.89% | 9 / 9 | 4 / 4 | 41 / 41 |
| 903 | revised | `numPermsDISequence` | js | 843 | 843 | 529 | 0.00% | -37.25% | -37.25% | 12 / 12 | 4 / 4 | 41 / 41 |
| 250 | control | `countUnivalSubtrees` | py | 1,328 | 1,262 | 795 | -4.97% | -37.00% | -40.14% | 19 / 19 | 4 / 4 | 49 / 49 |
| 250 | control | `countUnivalSubtrees` | js | 1,321 | 1,360 | 894 | +2.95% | -34.26% | -32.32% | 15 / 15 | 4 / 4 | 49 / 49 |
| 270 | control | `closestValue` | py | 1,136 | 1,071 | 640 | -5.72% | -40.24% | -43.66% | 18 / 18 | 4 / 4 | 49 / 49 |
| 270 | control | `closestValue` | js | 1,205 | 1,224 | 770 | +1.58% | -37.09% | -36.10% | 17 / 17 | 4 / 4 | 49 / 49 |
| 737 | control | `areSentencesSimilarTwo` | py | 743 | 682 | 351 | -8.21% | -48.53% | -52.76% | 14 / 16 | 3 / 3 | 31 / 31 |
| 737 | control | `areSentencesSimilarTwo` | js | 995 | 1,002 | 573 | +0.70% | -42.81% | -42.41% | 15 / 17 | 3 / 3 | 31 / 31 |
| 1214 | control | `twoSumBSTs` | py | 681 | 615 | 370 | -9.69% | -39.84% | -45.67% | 15 / 15 | 3 / 3 | 39 / 39 |
| 1214 | control | `twoSumBSTs` | js | 816 | 832 | 537 | +1.96% | -35.46% | -34.19% | 15 / 15 | 3 / 3 | 39 / 39 |

## 4. Reproducibility Commands

```bash
python3 projects/algorithm_solver/catalogue/development-66-20261029-v1/measure_canonicalization.py
python3 -m unittest projects/algorithm_solver/catalogue/development-66-20261029-v1/test_canonicalization.py
```
