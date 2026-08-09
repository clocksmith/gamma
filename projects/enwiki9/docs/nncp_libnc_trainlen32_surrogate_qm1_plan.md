# NNCP LibNC Train-Length-32 Surrogate Qm1

Status: frozen source-native surrogate gate

## Purpose

The exact ROCm 32/32 child saved 4,791 bytes at 65,536 symbols by updating
after 32 completed states, rebuilding its KV state, and updating again after
state 64. The held LibNC binary already exposes `--train_len 32`, which doubles
the update cadence without source edits. The source requires relative-position
width to equal memory plus training length, so the valid coupled profile uses
`d_pos=256+32=288`. It is a useful source-native test but is not numerically
identical: it also changes segment memory and relative-position geometry and
carries pre-update hidden states through native memory.

## Frozen gate

Run the native batch-32 `enwik9` profile twice at exactly 10,000 preprocessed
symbols with four CPU threads, `train_len=32`, its required `d_pos=288`
coupling, and the established `16384,512` preprocessor. Decode the first
archive through the native decoder.

The exact parent archive is 9,246 bytes. Require two byte-identical candidate
archives, exact nonempty raw-prefix reconstruction, at least 500 actual bytes
of archive reduction, and a passing outer decimal-memory guard. The executable
and library are unchanged, so incremental submitted program bytes are zero.

A miss retires only this built-in surrogate and opens no train-length sweep. A
pass authorizes engineering the exact post-midpoint update-and-rebuild contract
inside the native source. Neither outcome inherits the published NNCP score.
