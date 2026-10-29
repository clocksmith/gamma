# P–U, L/M, N/O and Q results, 2026-10-28

Each lane was run on the Linux executor from a detached worktree, then replayed on the host without execution. Every replay matched its report. The worktrees were `b1dde1a1e` (P, R, T, U, L/M) and `6485ec371` (S, N/O, Q). All lanes used the existing six-anchor gate (`dfeb3df2…`), the shared passing preflight and unchanged limits: 3 CPU seconds, 8 wall seconds and 1 GiB per batch. Raw streams, reports and replays stay in the executor's `gamma-continuation-20261028` run directory. Problem statements and generated cases were never copied off the executor. Nothing here changes catalogue admission or adoption.

## Summary

| Lane | Controller | Programs | Qualified | Calls | Batches |
|---|---|---:|---:|---:|---:|
| P | [p v1](../continuation-p-qualification-20261028-v1/README.md) | 20 | 20 | 14,828 | n/a |
| R | [r v1](../continuation-r-qualification-20261028-v1/README.md) | 12 | 12 | 15,020 | 484 |
| T | [t v2](../continuation-t-qualification-20261028-v2/README.md) | 16 | 13 | 4,526 | 166 |
| U | [u v1](../continuation-u-qualification-20261028-v1/README.md) | 2 | 2 | 3,486 | 106 |
| S | [s v2](../continuation-s-qualification-20261028-v2/README.md) | 20 | 17 | 4,390 | 168 |
| L/M | [lm v1](../continuation-lm-qualification-20261028-v1/README.md) | 40 | 18 | 9,444 | 354 |
| N/O | [no v1](../continuation-no-qualification-20261028-v1/README.md) | 46 | 20 | 18,284 | 634 |
| Q | [q v1](../continuation-q-qualification-20261028-v1/README.md) | 20 | 12 | 3,540 | 134 |
| **Total** | | **176** | **114** | | |

"Qualified" means qualified on that lane's finite suite only. The P batch count is not printed by the P replay.

## Binding hashes

| Lane | Freeze | Review | Report | Host replay |
|---|---|---|---|---|
| P | `30c7778d201292b11b5a44a65be1fca3428e15c1e018bd100a74a0bb5c69deb4` | in freeze | `a11f98f442961fb3689e554ba5c0519afb73742676ec52008be43cfc10bf4734` | `67cdaaf2675b2089850c0e5e8dfc4481decbef05a31be5d9c7cd62acfabc0032` |
| R | `697f53bcfbd41ea4d18eca06aa444aa68e79414ae0e9975d015de11774e68282` | in freeze | `56ee882fb6f2ad05b85481a3154055e8fe6b672d50a5ff69d2f7566712390373` | `a400c7bdc47bf24a59cd66780c06eb3f74d2024c60a8cb95dee89e3d625b71a8` |
| T | `e6437cdf87651c50db5433307b7bf6ae510e5f5d3b294f36c591e22c851e8277` | in freeze | `8f7a80eb97d35c6d4ba7fe18315b81afbd6546c2731dda1f8f6477f1169ad9c0` | `c16d5abdce9e353496821dea8ba819c5332adf6ac2c09087ce4c7981360e98e6` |
| U | `e34562e67b61fe5f2191f84b15b340fba29436e0aee8e61782ce5d75d4b825a2` | in freeze | `64fad97138abbb28fbe15939b02f96fffa529d5780f0757f2ce95f5b5d3ba5fe` | `4e257ae96268a3472fe2a0994647332061a476bbb801cf7d35c9ad64b3ea3e3e` |
| S | `466a277d75f34bdc21f3b96f99a871f1e12395d9e600e52c6913bbaac4c2f61e` | in freeze | `e426fe858dd76dd3a8aea5b30ff046639d0cbb0b5256b60dd8db372584290d6f` | `90fea54cf12a722a39445b55ab0f1ded8db3172584caf676cc962f23cf878bca` |
| L/M | `def367d21ec92ff84790c05a65f79415623254a5938c5499220a196af684be9c` | `097cd2bb5e5bf1d40506a8a87007e3144604a264f8cd5824fec4bc3cb8c85031` | `b75a54e72b14bd26f1bf1eb1c8be32be75729417cc81f17daf6ec6d6d5105bdd` | `ea6c16c35fe949de5622bdac9c35e172470de0edc6d0239d8d758b73566dc8c3` |
| N/O | `33c5d33cc405c3414374e42328bf7775af6953aa24fc392c523645c08df6458f` | `6cf6e3a299a345d9d8ffce1cca2854091f492de811be4d9500d159d683da4d70` | `1f15ad415ad82e6d2145baad5ab944edf185dba826cca68667ff928e0a99addf` | `2b9e70600bec23c2b769175872f7e7318de5c57be856ea64c1948fabaab8b56b` |
| Q | `6038aa548527883ea9cffbebbd3382996e1a6be68a908bb06e3355700aa59b41` | `430a0df8538ed8cd5287010441dd8e4ba594c36221a80bf4c377d0d525a88a21` | `dd9599044d994a2e1f533f23d97e6c5ea205ad44bbd8ff9e4ef44ce4ece28ca3` | `149739d2b40bc8dd5b23d6da82c70a0de207073382310abb94e8466fc93386b0` |

The S freeze uses the v2 controller. The S/T controller receipt pins the v1 response hash and does not apply to this run.

## Programs not qualified

### Killed at the CPU limit: 234, 235 and 236 JavaScript (T); 222 JavaScript (S)

These four JavaScript programs were killed (exit 137) at about 3.0 CPU seconds on the 100,000-node cases. Their Python versions passed. The T observer's own stress receipt measures about 3.07 seconds for the observer alone on a 100,000-node tree under jitless Node. The observer therefore uses the whole budget before the candidate's cost is counted. This is an observer-cost failure, not evidence about the candidates. Raising the limit is not the fix.

### Transport-blocked: 208 Python and JavaScript (S)

Both passed the original finite suite. The required-domain witness is about 20 MB, which exceeds the 16 MiB transport envelope. The lane records this as a required-scope blocker. It allows no cap raise, trace split, compression or omission.

### Case-set gaps: 28 problems, 56 programs (L/M, N/O, Q)

These programs passed every executed case or, in Q, were not dispatched. Their mandatory review set `independent_references_and_boundaries` to false. In every L/M and N/O case, both languages' reviews give the same reason. The reviewers found no source defect except in 3937, below.

| Problem | Gap a plausible wrong program would pass |
|---|---|
| 3855 | No 5 ≤ k < 10^9; the large-k expected value reuses the candidate formula. A floating-point power mutant passed. |
| 3859 | No maximum case with many distinct values, so an O(n·D) program passes. |
| 3862 | No case with two balanced indices or a large balanced sum. Largest-index and int32 mutants passed. |
| 3869 | Only windows of width ≤ 100, where prefix errors cancel. A mutant mishandling 6+ digit numbers passed. |
| 3872 | Only lengths 4–8 plus trivial maxima. |
| 3873 | Only a 4×4 grid plus a diagonal and a line. |
| 3876 | Only lengths ≤ 8 plus uniform-parity maxima. |
| 3877 | Only n ≤ 8 with values ≤ 15, plus all-equal n = 40. |
| 3878 | Only n ≤ 8 with values ≤ 31, plus uniform maxima. |
| 3881 | Random n ≤ 8; large n only at k ∈ {0, 1, n−2, n−1} and one middle value. |
| 3885 | Random traces of at most 8 events; the maximum is a single priority. |
| 3891 | No length above 5 and no value near 10^9. |
| 3896 | No value near the 10^5 bound. |
| 3897 | Maximum n = 10^5 absent; no large mixed segments. |
| 3901 | Small random rows plus one p = 1 maximum. |
| 3905 | Grids up to 5×7 plus one two-source line. |
| 3909 | Never an equal-sum answer (−1), a peak at either end, or sums above 2^31. |
| 3915 | Length-14 random rows plus two maxima. |
| 3919 | n ≤ 15 plus one endpoint-query maximum. |
| 3926 | Small random strings plus one uniform maximum. |
| 3932 | r ≤ 10,000 except two analytic rows. |
| 3934 | Random length ≤ 50 over small alphabets plus two periodic maxima. |
| 3937 | References capped at k ≤ 15. The statement is ambiguous about negative values and `%`, and the reference shares the candidate's reading (also `independent_source_review` false). |
| 3942 | Only permutations of n ≤ 6 plus two maxima. |
| 126 (Q) | Reachable cases have at most 8 three-letter words; the 500-word case has no reachable end. A partial-path-copy BFS passed. |
| 129 (Q) | No right-only child and no near-maximum sum. A "left is None means leaf" mutant passed. |
| 140 (Q) | Dictionary at most 13 words; an unpruned DFS passed. |
| 144 (Q) | No right-skewed chain. A misplaced right-push mutant passed. |

In Q, unapproved programs receive no dispatch, so these eight programs were not executed.

## Boundary repair of the 28 case-gap problems

Each repair lane holds every original case for its problems plus new boundary cases whose expected values come from independent references. An independent reviewer that wrote neither the cases nor the sources recomputed every new row (0 mismatches), confirmed that each named wrong program now fails a row, and set every review flag from its own flag-by-flag source verdicts. Limits, observers, transport and comparisons are those of the lane being repaired.

| Lane | Programs | Qualified | New rows | Calls replayed | Batches | Freeze | Review | Report | Host replay |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| [Q boundary](../continuation-q-boundary-20261028-v1/README.md) | 8 | 8 | 315 | 1,534 | 214 | `e947d63748f2b2da4e0f1f703676c8be7209bbcab5e1b84f300787547414256e` | `8902a838c3a5d8c9c0ac06298f8defa65370ee32653efa54ab5552fba603bcb1` | `4c046c161e1a70293757ae0faa85199b27da354d8e0019271d8684f0a8a52076` | `64df7ba83eb96a7bada853b49a0ed73bc0da96fd6344cb6192041ea04e06d69b` |
| [L/M boundary](../continuation-lm-boundary-20261028-v1/README.md) | 22 | 22 | 1,261 | 5,706 | 376 | `258426879befa19ce4c8efa02ea15d75281d38306594d6674f77fd1e8c5c80e6` | `d79e91b0bfaaa24f3ab065606ee58f202705a4e14bb288003b3bfcbd7d67c400` | `e6ccf8e3b33c9f64462385d197b53878bb76da5239efea731073122530124e4d` | `f9e63f9a643a07c52d58b73549bf06d314c3585b8b2c7a62d0a6197a7b4d7c1e` |
| [N/O boundary](../continuation-no-boundary-20261028-v1/README.md) | 26 | 26 | 638 | 13,350 | 690 | `3229f1cfdb0512bd8d0d20352df30a06e6126bd2591c941bf2141e619c805c2e` | `d60846ae358939068610667b8818d0d9fbaff4bb53a94294714747fd3cc22dd0` | `4809aa4734b2e130903bdffe46dad51e854b2c9fe435d77099601b151c8cc735` | `087de467b2ec806127dcae62921110438f9941323f375b47243cc6163123f75b` |

All 56 programs qualified on their repaired finite suites, and every replay matched. Combined with the table above, 170 of 176 programs are now qualified. The remaining six are the four observer-cost kills and 208 in both languages.

Caveats recorded by the reviewers:
- **140:** an unpruned DFS is rejected only by the complexity review; its JavaScript CPU rejection on the dead-end batch depends on hardware.
- **3862:** the "two balanced indices" gap is impossible in the domain (values are at least 1), so it was closed by proof, not cases.
- **3937:** the circular-residue reading was adopted by the lane operator on third-party evidence (the doocs reference). It is not an owner decision.

## Observer-cost reruns: 234, 235, 236 and 222 JavaScript

The [v2 observers](../continuation-t-observers-20261028-v2/README.md) ([S](../continuation-s-observers-20261028-v2/README.md)) perform the same checks as v1 with byte-identical verdicts on every equivalence test, at about a quarter of the CPU cost on 100,000-node inputs. An independent review found one Proxy-on-class-chain divergence, which was fixed and re-reviewed (129,360 fuzz cases, 0 mismatches). Independent source, observer and controller reviews were pinned in the [T v3](../continuation-t-qualification-20261028-v3/README.md) and [S v3](../continuation-s-qualification-20261028-v3/README.md) controllers. Limits are unchanged.

| Lane | Programs | Qualified | Calls | Batches | Freeze | Report | Host replay |
|---|---:|---:|---:|---:|---|---|---|
| T v3 | 3 | 3 | 731 | 31 | `cee0a50771a8f71554d2dc477009f0ed26255a8bdc1999a798e4c6e70b0d5098` | `40517a65a442ba9a19be54419a9edc7b630b673b82273e96f19f3dd990a0ab83` | `44e9dbc231f893a85c0147b95779f7d4ba1d4d2b284ea47eee9518f1cbe9bbca` |
| S v3 | 1 | 1 | 146 | 8 | `42a9174e01eca3360d194fe1335c0e04f2f2caf754ecfdbb83b95113a59fe524` | `16fe5c73be8629bfb12b646b363e74a69f1984fab58c7f21e001c333131598eb` | `329be0027beb606d8970fa79e225c8c0ae40fb46143cfb68b4cc0b9696dbcf58` |

All four programs qualified and both replays matched. **174 of the 176 continuation programs are now qualified.** The two remaining are 208 in Python and JavaScript, blocked by the transport envelope.

## Next

1. Done: see the boundary repair section above.
2. Done: see the observer-cost reruns above.
3. 208 needs a transport profile that can carry the 20 MB witness without the forbidden workarounds.
