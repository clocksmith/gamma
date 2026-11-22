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
