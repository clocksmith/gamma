# Seal-2 Route E: State-Preserving Prototype Bypass

Status: frozen Q0 contract, zero score credit until native counted replay.

Candidate: `seal2_route_e_state_preserving_prototype_bypass_q0_v1`

## Proof target

Route E tests a new coding operation over the exact endpoint428 parent trace:

```text
BYPASS_COPY(source, length)
```

The decoder reconstructs the next WRT bytes from already decoded WRT bytes,
does not consume arithmetic truth bits for that span, and must still present
every reconstructed bit to the parent predictor update path. Q0 uses the exact
parent P1 trace to measure this operation without changing native Gamma source.
It has zero forecast and score credit.

The official objective remains a deterministic full-corpus result with score
at most 108,000,000 bytes. The current source-bound forecast is 109,389,323,
leaving 1,389,323 bytes, or 1,389.323 B/M, of forecast debt.

## Bound inputs

Q0 uses the receipt-bound opening-1M endpoint428 artifacts:

- `results/endpoint428_pair_layer0_online_native_1m_v1/receipt.json`
- exact `CMX21P1` final-probability trace
- exact WRT store and English dictionary
- exact parent archive
- exact raw reconstruction

The gate must verify the recorded SHA-256 values, reproduce the 173,859-byte
parent arithmetic payload byte-for-byte, and bind the reconstructed WRT store
to the exact 1,000,000-byte raw SHA-256 through the official WRT inverse.

## Frozen population

Map complete raw `<page>...</page>` spans to exact WRT-byte boundaries. Let
`N` be the complete-page count in chronological order.

```text
development          page indices [0, floor(3N/5))
selection            page indices [floor(3N/5), floor(4N/5))
sealed_confirmation  remaining page indices
```

The format, codes, minimum copy length, prototype rule, and source accounting
are frozen before reading split results. Only prior complete pages are legal
prototypes. The first page is necessarily literal.

## Frozen alignment universe

Q0 permits exactly one prototype page per target page. Every earlier complete
page is evaluated as a candidate prototype.

For a target/prototype pair, a reversed suffix automaton identifies the
longest exact prototype match beginning at each target WRT byte, with the
lowest encoded source offset used as the deterministic occurrence tie-break.
Every prefix length from 8 bytes through that longest match is legal. An exact
backward dynamic program selects non-overlapping copies under the frozen
integer objective:

```text
displaced parent P1 qbits - 2048 * encoded copy-command bytes
```

Parent qbits use the exact 1/256-bit table. The dynamic program is only the
selection objective; all reported promotion economics use constructed and
terminated arithmetic payloads.

## Frozen command format

Unsigned integers use canonical ULEB128. The command stream is finite and is
not compressed by an uncounted model.

```text
u32 active_page_count
repeat active pages in target order:
    uleb target_page_wrt_start
    uleb target_page_wrt_length
    uleb prototype_page_wrt_start
    uleb prototype_page_wrt_length
    u32 copy_count
    repeat copies in target order:
        uleb target_offset_within_page
        uleb source_offset_within_prototype
        uleb copy_length
```

Inactive pages and all uncovered bytes are literal. Copy intervals must be
non-overlapping, remain within their pages, reference a strictly earlier page,
and reproduce exact WRT bytes.

The candidate archive contains an eight-byte magic, fixed-width WRT length,
trace-row count, command length, literal-bit count, and literal-payload length,
followed by the command stream and the actual range-coded literal payload.

## Controls

- E0: exact parent replay over every WRT truth bit. Its payload must equal the
  receipt-bound parent payload byte-for-byte.
- E1: at most one contiguous exact copied span per target page, selected from
  one earlier prototype page with complete command cost.
- E2: multiple separated copied spans with literal holes against one earlier
  prototype page. This is Route E.
- ER: rotate E2's selected prototype page distances chronologically, repair
  them deterministically to remain prior, then recompute the exact alignment.

For E1, E2, and ER, the command stream must roundtrip, the literal arithmetic
stream must decode, the WRT stream must reconstruct exactly, and a second
archive construction must be byte-identical. E2 must also pass the official
WRT-to-raw inverse and reproduce the exact raw hash.

## Exact accounting

For control `E`:

```text
T(E) = literal arithmetic payload bytes
     + command bytes
     + fixed archive frame bytes
```

The gate records both the directly measured compressed source size of the
candidate program plus gate and a conservative full-corpus source allowance
equal to that measurement. Source is amortized once over the projected 1G
corpus; it is never hidden in the command or payload totals.

Split receipts rebuild an otherwise-literal archive with only that split's E2
plans enabled. This measures exact development, selection, and confirmation
signs without attributing non-additive range-coder finalization by log loss.

## Promotion and kill gates

All of the following are required for one frozen 10M replay:

```text
gross exact E2 gain versus E0             >= 3,000 B/M
projected net after source allowance       >= 2,100 B/M
E2 total bytes                             < E1 total bytes
E2 total bytes                             < ER total bytes
selection-only exact gain                  > 0 bytes
confirmation-only exact gain               > 0 bytes
parent payload identity                    exact
command stream roundtrip                   exact
WRT reconstruction                         exact
raw reconstruction                         exact
second archive                             byte-identical
```

A miss retires unchanged prior-page, single-prototype Route E Q0. Do not sweep
minimum copy length, prototype count, integer code, page-distance window, or
multiple-prototype composition. The materially different successor is a
transmitted many-use corpus grammar bypass with its own upper-bound
certificate.
