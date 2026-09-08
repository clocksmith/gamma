# BUILD — exact reproduction of the submitted binaries

## Toolchain (as used for the submitted build)

- Ubuntu 24.04.4 LTS, kernel 6.17.0-35-generic, x86_64
- clang++ 17.0.6 (Ubuntu), llvm-profdata-17 (PGO)
- upx 4.2.2 (`upx-ucl`)
- GNU make

## Exact candidate build

The build script `build_and_construct_comp.sh` defaults to a different
baseline configuration. From the source-directory root, the submitted
candidate was built with this environment:

```bash
export EXTRA_CFLAGS_DEFINES='-DFX3_LSTM_CELLS=300 -DFX3_LAYER1_LR=0.0001 -DFX3_LSTMEX_BIT_HINT_SCALE=256 -DFX3_LAYER1_BYTE_MIXER_INPUT_SCALE=0 -DFX3_ENABLE_FXCM_V26=1 -DFX3_FXCM_V26_GROUP_MASK=23 -DFX3_FXCM_V26_AUX_MASK=1 -DFX3_FXCM_V26_COMPACT_OUTPUTS=1 -DFX3_FXCM_V26_AUDIT_INPUT_COUNT=1 -DARCHIVE9_DYNAMIC_SPLIT_HEADER -DFX3_ENABLE_HEAP_THP_ADVISE=0 -DFX3_ENABLE_ANON_THP_ADVISE=1'
export FX3_FINAL_CFLAGS_DEFINES='-UFX3_LSTM_CELLS -DFX3_LSTM_CELLS=270'
export FX3_UPX_MODE=9
FX3_SEED=923 FX3_UPDATE_LIMIT=3000 bash ./build_and_construct_comp.sh
```

The seemingly redundant LSTM definitions are intentional and reproduce the
recorded compiler command: the inherited v26 configuration first supplies
300 cells, then `FX3_FINAL_CFLAGS_DEFINES` replaces that value with the
effective candidate value of 270. Do not simplify this sequence when trying
to reproduce the recorded build.

The build performs PGO (`prof_gen` -> training run -> `prof_use`) and packs
the final binary with `upx-ucl -9`. The authoritative machine-readable build
record is `build-manifest.tsv`; the exact expanded compiler commands are in
`canonical-build.log`, both in the same directory as this file. These two
files contain the candidate markers `group_mask=23`, `aux_mask=1`, and
`effective_lstm_cells=270`.

The files `build.log`, `build-fixed.log`, their stderr companions, and
`docs/canonical-build-historical-full-v26.log` are retained historical build
records. They are not the canonical provenance for this submission.

## Reproducibility notes (honest)

- The recorded canonical build produced the submitted wrapper byte-for-byte:
  `candidate_wrapper_bytes=462290`,
  `candidate_wrapper_sha256=d11595b6...88294fd`. `build-manifest.tsv` also
  binds the cumulative source patch as
  `source_patch_sha256=d19eed8e...dcaa0`.
- The makefile uses `-march=native` by default. Bit-identical binary
  reproduction therefore requires the same microarchitecture (Comet Lake);
  `COREI7=1` (`-march=corei7`) is provided as a portable alternative and is
  the recommended setting for verification machines. Functional behaviour
  (compression output) is architecture-independent; the canonical-build log
  documents the exact flags used for the submitted binary.
- PGO profiles introduce build nondeterminism across environments; the
  authoritative binary identity is the shipped `cmix`/`archive9` pair and
  their SHA-256 values, not a re-build hash.
