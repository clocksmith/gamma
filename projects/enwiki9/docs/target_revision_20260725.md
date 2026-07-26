# enwiki9 Target Revision - 2026-07-25

## Decision

Gamma now uses a three-level target hierarchy:

```text
engineering checkpoint       <= 109,000,000 bytes  (10.9000000%)
prize-competitive gate       <= 108,500,000 bytes  (10.8500000%)
canonical design target      <= 108,000,000 bytes  (10.8000000%)
scope_bytes                  == 1,000,000,000
roundtrip_ok                 == true
```

Research economics, candidate promotion, and target-distance reporting use the
`108,000,000` canonical design target. The other thresholds remain visible as
progress checkpoints; they are not stopping conditions. This hierarchy
supersedes the prior `109,500,000` (`10.9500000%`) objective. Historical
receipts retain their original target and margin fields.

## Benchmark Evidence

Matt Mahoney's Large Text Compression Benchmark lists the June 2026
`cmix-lex` self-extracting `archive9` at `109,190,109` bytes:

```text
https://mattmahoney.net/dc/text.html#1091
```

The Hutter Prize's June 27 comment-period announcement reports independently
reproduced accounting as:

```text
compressor/source package       470,599
reproduced archive          109,201,040
counted submission total    109,671,639
```

Source:

```text
https://groups.google.com/g/Hutter-Prize/c/HTCx_bC9C5M
```

The benchmark archive and counted prize submission remain separate quantities.

## Prize Threshold And Cushion

A further one-percent improvement over the reproduced counted total requires:

```text
0.99 * 109,671,639 = 108,574,922.61
integer threshold          < 108,574,923
maximum qualifying score     108,574,922
```

The `108,500,000` gate is `74,923` bytes below the exclusive threshold. The
`108,000,000` design target is `574,923` bytes below it, providing room for
full-corpus transfer decay, package growth, calibration error, and competitive
movement.

## Effect On Current Frontier

The current counted forecast of `109,389,323` has these distances:

```text
engineering checkpoint   109,000,000 - 109,389,323 =   -389,323 bytes
prize-competitive gate   108,500,000 - 109,389,323 =   -889,323 bytes
canonical design target  108,000,000 - 109,389,323 = -1,389,323 bytes
```

It remains a constructive-prefix forecast, not a full-corpus result. Runtime,
memory, exact full-1G accounting, and deterministic roundtrip requirements are
unchanged.
