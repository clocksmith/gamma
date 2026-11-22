# BITS six-bit compact proof reproducibility sidecar

The package contains an extraction/checking driver, not a copy of the Gamma
corpus or any dataset prompts. The required bytes are retained in the public
[Gamma source pin](https://github.com/clocksmith/gamma/tree/59ff04415ff2afd04ff2ed451340f4f02852bf18/projects/algorithm_solver/literals/sixbit-v1).

Run this driver with an existing Gamma checkout containing the pinned commit, using Git and Python 3:

    python3 verify_bits.py /path/to/gamma

If the exact commit is absent, fetch it from the authorized Gamma remote first.
`verified-output.txt` is the expected stdout from the pinned checker.

The driver never checks out or mutates Gamma. It reads Git blobs from the full
pinned commit, verifies the 80 exact compact sources against manifest SHA-256s,
checks the 74-singleton elementary witness lower bound, runs the retained
no-solver checker against the compact A, B, and C (`literal-escape6-v1`) runs,
and verifies that every `dictionary.ltd` (including decoded escape packets)
unpacks to the exact `manifest['vocabulary']` checked for rule eligibility.
Nothing runs the 80 JavaScript programs or reruns optimization. Validation uses
a temporary directory that is removed on completion.

The compact A (`U=79`, `W=92`) and C (`c-w-compact=75,925`, implied raw bound
`65,079`, raw recount `65,236`; `c-u-compact=24,613`, bound `24,166`) checks use
the frozen Mars `run-v1` arms; compact B (`U=W=64/80`) uses the frozen Mars `W`
arm and the Jupiter `U` supplement on the same compact inputs. This sidecar does
not check canonical-source runs or Phase-2 selection optimality.

## Second implementation and negative test

- Independent checker, written from the written rules and frozen artifacts without
  importing any existing checker or decoder:
  [`../independent-verifier/`](../independent-verifier/README.md), added in Gamma
  `bfd8a5222`. From Gamma's root:
  `python3 -B -m unittest discover -s projects/algorithm_solver/literals/sixbit-v1/independent-verifier -v`
  (11 tests: the frozen reproduction, six mutation tests and tiny exhaustive oracles).
- Slot-swap negative test: [`test_escape_slot_swap.py`](test_escape_slot_swap.py).
  It swaps two entries of the frozen `c-w-compact` manifest vocabulary while keeping
  `dictionary.ltd` and every `.lte` packet fixed. The checker frozen at the source pin
  accepts that fixture with an identical report (75,925 presses); the current
  `../verify_amended.py` rejects it. From Gamma's root:
  `python3 -B -m unittest discover -s projects/algorithm_solver/literals/sixbit-v1/reproducibility -v`

## Certificate and artifact specification

Enough to re-implement both checks from this text. All integers are big-endian; all
strings are UTF-8.

**Sources.** The 80 programs are the `compact` rows of
`scale-v2/generated/manifest.json` whose `id` is in `matched80-v1/labels/ids.json`,
keyed by `str(id)`; each file's SHA-256 must equal its row's `sha256`. Positions in a
program are character (code point) offsets `0..n`.

**Eligibility.** A string `s` is eligible when it is non-empty, occurs in at least one
program and is not equal to a whole program. Under `U` that is all. Under `W` a string
longer than one character must also be at most 160 UTF-8 bytes and occur in at least
two distinct programs; single characters are always eligible.

**`certificate.json`.** `{kind, scale, mu, potentials}`. `kind` is `A`, `B1` or `C`;
`scale` is a positive integer denominator (here 2^20); `mu` is a non-negative integer,
the budget multiplier times `scale`, in the objective's units per dictionary slot
(programs for `B1`, presses for `C`; unused for `A`); `potentials` maps each program
key to `n + 1` integers `p_0..p_n`. Any values give a valid bound; the solver is only
trusted to have found good ones.

**Bounds.** For an occurrence of `s` at `i..j` define the reduction
`r = max(0, p_i - p_j - sigma)`, and for each eligible `s` the term
`T_s = min(0, kappa - sum of r over all its occurrences in all programs)`. With
`N = 80`, `D = scale`:

| Kind | `kappa` | `sigma` | Bound numerator `B` | Claim |
| --- | --- | --- | --- | --- |
| A | `D` | 0 | `sum_p (p_0 - p_n) + sum_s T_s` | entries >= `ceil(B / D)` |
| B1 | `mu` | 0 | `N*D - 64*mu + sum_p min(0, p_0 - p_n - D) + sum_s T_s` | uncovered >= `ceil(B / D)`, so coverage <= `N - ceil(B / D)` |
| C | `mu` | `7D` | `sum_p (p_0 - p_n) - 63*mu + sum over escapable characters at i of min(0, 15D - p_i + p_(i+1)) + sum_s T_s` | presses >= `ceil(B / D)` |

Escapable characters are newline and code points 32 to 126. In C, a dictionary
selection costs 7 presses and an escape 15 (frozen framing: one press per code bit, 6 or 13,
plus one).

**Run folders.** `run-v1/<experiment>-<rule>-<style>/` holds `manifest.json`
(`vocabulary`: the ordered list checked for eligibility; `selections`; for C also
`presses` and `escapes`), `certificate.json` and, where a packaged encoding exists,
`dictionary.ltd` and `packets/<program key>.ltv` (A, B) or `.lte` (C).

**`dictionary.ltd` (LTD1).** `"LTD1"`, a u32 entry count, then per entry a u32 byte
length and the entry bytes, with nothing after the last entry. Slot `k` is entry `k`,
and the decoded list must equal `manifest.vocabulary` exactly and in order.

**`.ltv` (LTV1, A and B).** Byte 4 is the code width (6); bytes 37..40 are the u32
selection count; the codec is `readable-v1/literal_codec.py` at the pin.

**`.lte` (C).** Bytes 36..39 are the u32 token count; the code stream starts at byte
40. Each token is a 6-bit code: values 0..62 select that dictionary slot; 63 is ESC,
followed by a 7-bit character code. Decoding all tokens must reproduce the source
bytes exactly.
