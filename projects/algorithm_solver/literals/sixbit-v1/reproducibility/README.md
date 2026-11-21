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
and runs the original amended no-solver checker against the retained receipts,
vocabularies, dictionaries, packets and certificate potentials. Nothing runs
the 80 JavaScript programs or reruns optimization. Validation uses a temporary
directory that is removed on completion.

The compact U/W entry minima use the frozen Mars arms; compact B coverage uses
the frozen Mars W arm and the Jupiter U supplement on the same compact inputs.
This is not a check of canonical, escape-mode, or phase-2 optimal token counts.
