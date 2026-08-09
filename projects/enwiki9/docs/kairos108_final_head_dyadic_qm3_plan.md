# KAIROS-108 final-head dyadic opening gate QM3

Candidate: `kairos108_final_head_dyadic_qm3_v1`

Parent: `kairos108_final_head_dyadic_qm2_v1`

Status: frozen linker infrastructure repair; zero score credit.

## Single change

QM2 found the pinned Clang 17 compiler and successfully compiled every observer
translation unit. Linking then failed because the donor Makefile defaults to
`-fuse-ld=lld`, but that linker is absent from the pinned toolchain. This child
uses the repository's established cmix build contract and overrides `LFLAGS`
to select the available system `bfd` linker while retaining PGO and LTO flags
added by the unchanged `prof_use` target.

No observer record, modeled object, probability feature, rank, quantization,
atomic interval, correction law, dynamic program, control, schedule cost,
arithmetic coder, donor asset, or opening scientific gate changes.

## Required arms and decision

Run unchanged `B0`, `G0`, `K0`, `P0`, `R0`, `S0`, and `O0` over the first
`1,000,000` raw bytes. Require traced-parent payload identity, exact `B0` and
`K0` range replay, repeat identity, legal probabilities, and a paid schedule no
larger than `128 KiB`. Require at least `4,500` K0 gross bytes, positive gains
in every chronological third, and at least `500` bytes over every matched
control. A scientific miss retires this KAIROS realization.
