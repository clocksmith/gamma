# NNCP Evicted-State EMA Memory QM0

Status: frozen 65,536-symbol constructive child; zero score credit.

## Question

Does a single decoder-built summary of NNCP hidden states that have just fallen
outside the 256-position attention memory add target-bearing information without
adding parameters or resident memory?

## Frozen mechanism

For every layer and native stream, retain 255 exact recent hidden states. The
oldest memory slot contains a bfloat16 exponential summary. At each existing
64-symbol update, average the 64 oldest exact slots excluding the prior summary,
then update:

```text
summary_next = 0.5 * summary_previous + 0.5 * mean(oldest_64_exact_states)
```

The summary occupies the same tensor slot it replaces. Attention, relative
position logic, model parameters, arithmetic alphabet, optimizer, update
schedule, incremental-KV prediction path, and exact NNCP inverse remain
unchanged. Encoder and decoder rebuild the summary from already known states.

## Gate

Compare against the receipt-bound faithful 96,142-byte archive over exactly
65,536 symbols. Require two encoders and one decoder to reproduce identical
archives, branch frequencies, symbols, losses, and complete states; require the
official NNCP inverse; and require allocated and reserved device memory below
decimal 10 GB.

Promotion additionally requires at least 800 actual archive bytes and positive
aligned ideal branch gain in every true corpus-chronological third. The
compressed incremental diagnostic source must not exceed 65,536 bytes.

A miss retires this one-slot, decay-0.5, oldest-64 mean mechanism. There is no
decay, slot-count, pooling, or context-length rescue sweep. This finite gate
cannot inherit NNCP's published score and makes no full-corpus forecast.
