"""ari_codec — PPM-A class arithmetic coder with escape from order-3
down to order-0, with a final uniform 1/256 fallback.

The rationale for escape: pure higher-order n-gram on small scopes is
worse than lower-order because most high-order contexts are unseen. With
PPM-A escape, the model uses the highest seen context for each byte and
falls back automatically when the higher context has no information.

For each byte b at the current state (last 3 bytes of context):
  1. Try order-3 context. If never seen, no bits emitted, try order-2.
  2. Try order-2 context. Same rule.
  3. Try order-1.
  4. Try order-0 (single global context).
  5. Final fallback: uniform 1/256.

At any "seen" context with total count T:
  - Reserve 1 unit out of T+1 for the escape symbol.
  - If byte b has count c > 0 at this context: encode (cum_low, cum_low+c, T+1).
  - If c == 0: emit escape (T, T+1, T+1) and try the next-lower order.

Update: after each byte, increment the count of b in EVERY order's context
(including order-0 and the per-order contexts that were and were not used
for prediction this step). This is the PPM update rule.

Encoder/decoder lockstep: both maintain identical model state. Decoder
queries cum table at each order, decides escape vs symbol based on
target's interval, advances range coder. Both run identical updates
after each decoded byte.

Output:
  4B big-endian length (uncompressed bytes)
  N bytes range-coded payload
"""

from __future__ import annotations

import struct
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()))

import range_coder as RC

ORDERS = [3, 2, 1, 0]
MAX_ORDER = ORDERS[0]
ALPHABET = 256
MAX_TOTAL = 1 << 14  # rescale threshold per context
INITIAL_CTX = b"\x00" * MAX_ORDER


class PPMModel:
    __slots__ = ("counts",)

    def __init__(self) -> None:
        # counts[order][ctx_bytes] -> dict[byte -> count]
        self.counts: dict[int, dict[bytes, dict[int, int]]] = {
            o: {} for o in ORDERS
        }

    def get(self, order: int, ctx: bytes):
        return self.counts[order].get(ctx)

    def update(self, full_ctx: bytes, byte: int) -> None:
        """Increment count of `byte` in every order's context derived
        from full_ctx (last MAX_ORDER bytes)."""
        for order in ORDERS:
            ctx = full_ctx[MAX_ORDER - order :] if order > 0 else b""
            table = self.counts[order]
            entry = table.get(ctx)
            if entry is None:
                entry = {}
                table[ctx] = entry
            entry[byte] = entry.get(byte, 0) + 1
            # Rescale this context's counts when total grows large.
            if entry[byte] >= MAX_TOTAL // 2:
                # Halve all counts (with min 1) to stay within precision.
                new_entry = {}
                for k, v in entry.items():
                    nv = max(1, v >> 1)
                    new_entry[k] = nv
                table[ctx] = new_entry


def _cum_table(entry: dict[int, int]) -> tuple[list[int], int]:
    """Return (cum, total) for an entry. cum has length 257. total =
    cum[256]. Bytes with count 0 contribute 0 width."""
    cum = [0] * (ALPHABET + 1)
    s = 0
    for byte in range(ALPHABET):
        s += entry.get(byte, 0)
        cum[byte + 1] = s
    return cum, s


def pack(data: bytes) -> bytes:
    n = len(data)
    if n == 0:
        return struct.pack(">I", 0)
    model = PPMModel()
    enc = RC.RangeEncoder()
    full_ctx = INITIAL_CTX

    for byte in data:
        encoded_at_order = -1
        for order in ORDERS:
            ctx = full_ctx[MAX_ORDER - order :] if order > 0 else b""
            entry = model.get(order, ctx)
            if entry is None:
                continue  # context never seen at this order, no bits
            cum, total = _cum_table(entry)
            count = entry.get(byte, 0)
            if count > 0:
                cum_low = cum[byte]
                cum_high = cum[byte + 1]
                enc.encode(cum_low, cum_high, total + 1)
                encoded_at_order = order
                break
            else:
                # Escape
                enc.encode(total, total + 1, total + 1)
                # Continue to lower order
        if encoded_at_order == -1:
            # Final uniform fallback
            enc.encode(byte, byte + 1, ALPHABET)

        model.update(full_ctx, byte)
        full_ctx = (full_ctx + bytes([byte]))[-MAX_ORDER:]

    encoded = enc.finish()
    return struct.pack(">I", n) + encoded


def unpack(arch: bytes) -> bytes:
    (n,) = struct.unpack(">I", arch[:4])
    if n == 0:
        return b""
    payload = arch[4:]
    model = PPMModel()
    dec = RC.RangeDecoder(payload)
    full_ctx = INITIAL_CTX
    out = bytearray()

    for _ in range(n):
        byte = -1
        for order in ORDERS:
            ctx = full_ctx[MAX_ORDER - order :] if order > 0 else b""
            entry = model.get(order, ctx)
            if entry is None:
                continue
            cum, total = _cum_table(entry)
            target = dec.query(total + 1)
            if target >= total:
                # Escape
                dec.update(total, total + 1, total + 1)
                continue
            # Find byte whose interval contains target.
            # Binary search on cum (cum is monotonic).
            lo = 0
            hi = ALPHABET
            while lo < hi:
                mid = (lo + hi) // 2
                if cum[mid + 1] <= target:
                    lo = mid + 1
                else:
                    hi = mid
            byte = lo
            dec.update(cum[byte], cum[byte + 1], total + 1)
            break
        if byte == -1:
            # Final uniform fallback
            target = dec.query(ALPHABET)
            byte = target
            dec.update(byte, byte + 1, ALPHABET)

        out.append(byte)
        model.update(full_ctx, byte)
        full_ctx = (full_ctx + bytes([byte]))[-MAX_ORDER:]

    return bytes(out)
