Independent high-risk development review

From request-252-v1 run:
    python3 review/highrisk_tests.py --out review/highrisk_replay.json

The default candidate root is relative to review/highrisk_tests.py, so the command
works from any current directory. Use --root to select a different candidate root.
Python 3.10+ and Node.js are needed. No packages or network access are required.
Source hashes must match highrisk_review.json before candidate execution.

Coverage: 7 pairs, 4,961 cases per language (9,922 checks), plus 3 separately counted
maximum-shape probes in both languages (6 checks). The sources do not mutate inputs.
Tests independently enumerate or derive expected results; cross-language parity
alone is not used as an oracle. Candidates receive inputs only, not expected values.
Case generation is deterministic and checked against frozen case hashes.

Maximum-shape checks run sequentially. Each candidate process has a 65-second wall
timeout. Node uses a 256 MiB V8 heap cap; Python uses a 512 MiB POSIX address-space
cap and a 60-second CPU limit where available. --skip-maximum omits these 6 probes.

Source/statement access was authorized before review under the unchanged pinned
boundary. This portable replay neither acquires new content nor modifies access,
admission, serving, or qualification. It verifies the 14 specific candidate hashes.
Finite tests and manual review are not hidden-judge acceptance or universal proof.
