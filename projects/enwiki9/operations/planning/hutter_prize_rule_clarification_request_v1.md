# Hutter Prize rule clarification request v1

Status: draft, not sent

Subject: Clarification of memory, runtime-dependency, and score-accounting boundaries for an enwik9 submission

Dear Hutter Prize administrator,

We are preparing a deterministic, lossless, open CPU compressor for canonical one-billion-byte `enwik9`. Before presenting eligibility or resource claims, we would appreciate written clarification of several rule boundaries. These questions are prospective and do not ask you to evaluate or endorse a candidate result.

## Memory boundary

1. What exact byte ceiling does "10 GB RAM" mean: `10,000,000,000` bytes, `10 * 2^30` bytes, or another value?

2. What is the authoritative memory metric: peak resident memory, peak virtual memory, allocated heap, working set, cgroup memory, or another measurement?

3. Is memory aggregated over the compressor or decompressor process and all descendants, helpers, shells, and simultaneously resident subprocesses?

4. Does the ceiling cover every phase from process launch through preprocessing, compression or decompression, inverse transformation, archive construction, and cleanup?

5. Do brief peaks count? Would a cgroup-v2 hard limit plus continuous process-tree RSS and per-process high-water receipts be acceptable evidence?

6. Are operating-system page cache, memory-mapped file pages, shared-library pages, and shared pages charged to the submission? If so, by what accounting rule?

## Runtime and dependency boundary

7. Which runtime components are considered uncounted standard platform facilities, if any? Please classify the dynamic loader, C library, C++ runtime, compiler runtime, POSIX shell, core utilities, compression utilities, and operating-system locale or timezone data.

8. Must every shared object, helper executable, dictionary, model, table, script interpreter, and data file needed for compression or decompression be included in the counted submission unless explicitly classified as a standard platform facility?

9. May a submission dynamically link against system `libc`, `libm`, `libpthread`, `libstdc++`, or equivalent platform libraries? If yes, should their bytes be counted?

10. Is a compiler or build toolchain part of the counted artifact when source is supplied, or may evaluation build source using an evaluator-provided standard toolchain?

11. Is network access categorically forbidden during build, compression, and decompression? We intend to require a sealed, offline runtime.

## Score accounting

12. For a submission using the same program for compression and decompression, is the authoritative score exactly:

```text
compressed/self-extracting archive bytes
+ required program or source-package bytes
+ required option or command text bytes
+ every required nonstandard model, table, dictionary, runtime, and dependency byte
```

13. If compressor and decompressor are separate, please confirm whether the decompressor contribution is multiplied by two, and identify any exception.

14. May the self-extracting archive contain the decompressor, or must the decompressor also be supplied and counted separately? How should duplicated bytes be treated?

15. Are build scripts, manifests, licenses, attribution files, and reproduction instructions counted when they are required to produce or operate the submitted artifact?

16. Is archive framing, file metadata, executable headers, signatures, and padding counted exactly as submitted on disk?

## Runtime and execution

17. What CPU, operating system, core or thread allowance, compiler, and timing procedure determine the runtime limit?

18. Does preprocessing and inverse preprocessing count in compression and decompression runtime respectively?

19. Are SIMD instructions, profile-guided optimization, link-time optimization, transparent huge pages, and memory-mapped files permitted when source and exact build instructions are provided?

## Source, licensing, and attribution

20. May a submission incorporate GPL-compatible, fully attributed external compression code while claiming only the resulting submission score, provided complete corresponding source and license obligations are satisfied?

21. Does the prize require the submitter to be the original author of every component, or only to have the legal right to submit and publish the complete implementation?

22. What exact source, binary, license, attribution, build, and reproduction materials must accompany a candidate for official verification?

For each answer, please identify whether it is a binding interpretation for future submissions or informal guidance. We will preserve the response with its complete headers and content hash, and we will not broaden an answer beyond the question it directly resolves.

Thank you.

## Local provenance note

This draft was prepared against the content-addressed rule snapshots recorded by:

```text
projects/enwiki9/operations/provenance/hutter_prize_rules_20260822/receipt.json
```

No response has been received, and no official field may be changed from this draft alone.
