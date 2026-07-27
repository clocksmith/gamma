# ELF Load-Image Equivalence Problem

Status: independent constructive problem
Version: `ELI-1`

## Given

Let \(E\) and \(E'\) be finite ELF64 little-endian executable files for the
same machine. Define the loader projection \(\Lambda(E)\) to contain:

1. ELF identification, type, machine, version, entry point, flags, program
   header size, and program header count;
2. every program header in order, excluding only its file offset;
3. for each program header, the exact \(p_{\rm filesz}\) payload bytes to which
   its file offset points.

Section headers, section names, static symbols, and debug records are not in
\(\Lambda\).

Assume:

- \(\Lambda(E)=\Lambda(E')\);
- the operating system, arguments, environment, inputs, and shared libraries
  are equal;
- execution is deterministic under those inputs;
- the program does not inspect its own executable file, section table, static
  symbols, debug records, inode metadata, or pathname-dependent file bytes.

## Questions

1. Prove that the initial loader-created virtual-memory image and entry point
   are equal.
2. Prove that executions have equal state trajectories, output files, and exit
   status.
3. Deduce identical compressor archives and decompressor outputs.
4. Construct a finite verifier for \(\Lambda(E)=\Lambda(E')\).
5. Combine this result with EPT-1 and derive the exact counted package delta.
6. Explain why native archive identity and resource measurements remain
   mandatory despite the theorem.

