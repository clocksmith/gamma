"""ctw_codec — Context Tree Weighting (Willems, Shtarkov, Tjalkens 1995) +
range coder for prose-class data.

Self-referential trees of mutually recursive Venn Bayesian Monte Carlo
law-of-large-numbers prediction:
  - SELF-REFERENTIAL TREES: a binary tree of depth D where each node holds
    counts (a, b) of bits 0 and 1 seen at the contexts that reach it
  - MUTUALLY RECURSIVE: each node's WEIGHTED probability Pw is a mixture
    of its own KT estimate Pe and the product of its two children's
    weighted probabilities (recursion bottoms out at the leaf)
  - VENN: every byte of input contributes to multiple overlapping
    contexts simultaneously (from depth 0 up to depth D)
  - BAYESIAN: Pw_node = 0.5 * Pe_node + 0.5 * Pw_left * Pw_right is the
    Bayesian mixture under uniform prior over all bounded-depth tree
    models — this is the "CTW theorem"
  - LAW OF LARGE NUMBERS: as bytes accumulate, the KT estimator at each
    relevant context converges to the true conditional probability;
    the redundancy bound goes to 0 as N → ∞

Architecture:
  - Bytes split into 8 bits each, MSB first
  - Per-bit prediction uses last D bits of stream as context
  - All 8 bits share one CTW tree
  - Range coder encodes each bit at its CTW probability
  - Update tree after each observed bit (counts increment up the path)

The conditional next-bit probability is computed by:
  P(bit=0 | ctx) = β0 / (β0 + β1)
where βx is computed by walking root→leaf along the context, hypothesizing
the next bit is x at each node along the path, and combining via the
CTW recursion. We use log-probabilities and a running "log Pw" cache
per node to keep arithmetic stable.

For pure Python efficiency:
  - Sparse tree (Node lazily created on first visit)
  - O(D) work per bit = O(8D) per byte
  - For D=12, that's ~96 dict-lookup-class ops per byte

Output: 4B big-endian length, then the range-coded payload.
"""

from __future__ import annotations

import math
import struct
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()))

import range_coder as RC

DEPTH = 12
CTX_MASK = (1 << DEPTH) - 1
LOG_HALF = math.log(0.5)


class CTWNode:
    __slots__ = ("a", "b", "lpw", "left", "right")

    def __init__(self) -> None:
        self.a = 0  # count of 0-bits seen at this context
        self.b = 0  # count of 1-bits
        self.lpw = 0.0  # log(Pw) of all bits seen at this node
        self.left: CTWNode | None = None  # child for context-bit 0
        self.right: CTWNode | None = None  # child for context-bit 1


def _kt_log_increment(a: int, b: int, bit: int) -> float:
    """log(P_e_new / P_e_old) where Pe is KT estimator. For the next
    bit being `bit` given current counts (a, b)."""
    if bit == 0:
        # (a + 0.5) / (a + b + 1)
        return math.log((a + 0.5) / (a + b + 1.0))
    else:
        return math.log((b + 0.5) / (a + b + 1.0))


def _walk_path(root: CTWNode, ctx: int) -> list[CTWNode]:
    """Return list of nodes from root to depth-D leaf along the context
    bits (lazily creating nodes)."""
    path = [root]
    cur = root
    for d in range(DEPTH):
        ctx_bit = (ctx >> d) & 1  # most-recent bit first
        if ctx_bit == 0:
            if cur.left is None:
                cur.left = CTWNode()
            cur = cur.left
        else:
            if cur.right is None:
                cur.right = CTWNode()
            cur = cur.right
        path.append(cur)
    return path


def _log_add_exp(la: float, lb: float) -> float:
    """log(exp(la) + exp(lb))."""
    if la > lb:
        return la + math.log1p(math.exp(lb - la))
    else:
        return lb + math.log1p(math.exp(la - lb))


def _ctw_predict_log(path: list[CTWNode], hypothetical_bit: int) -> float:
    """Compute log Pw(root) HYPOTHETICALLY observing `hypothetical_bit`
    at the end of the current context. Walks from leaf upward, combining
    KT-incremented Pe at the current node with Pw at the (untouched)
    sibling. Children NOT along the path retain their existing lpw.
    """
    # Start at leaf: lpw_leaf_after = lpw_leaf + KT increment for bit
    leaf = path[DEPTH]
    lpw_below = leaf.lpw + _kt_log_increment(leaf.a, leaf.b, hypothetical_bit)

    # Walk upward
    for d in range(DEPTH - 1, -1, -1):
        node = path[d]
        # log Pe_new at this node = old + KT increment
        lpe_new = node.lpw + _kt_log_increment(node.a, node.b, hypothetical_bit)
        # Wait — this is wrong. node.lpw IS log Pw at this node,
        # not log Pe. Let me reconsider.
        pass
    # Simplified single-pass implementation: track lpe and lpw separately.
    raise NotImplementedError


class BinaryCTW:
    """Context Tree Weighting on binary alphabet, depth D.

    Each node stores counts (a, b) and three quantities derived from them:
      - log Pe_kt(node): KT estimator log-prob of all bits observed
        at this node
      - log Pw(node): weighted probability under CTW recursion
        Pw = 0.5 * Pe + 0.5 * Pw(left) * Pw(right)
        (interpret missing children as Pw=1, i.e., log 0)

    To predict P(next bit = b | context), we walk the path to the leaf,
    compute what Pw_root WOULD become if we observed bit b, and the
    answer is the ratio. In log-space:
      log P(bit=b) = lpw_root_after_b - lpw_root_now
    Both are computed bottom-up.
    """

    def __init__(self) -> None:
        self.root = CTWNode()

    def _walk(self, ctx: int) -> list[CTWNode]:
        return _walk_path(self.root, ctx)

    def predict_log_probs(self, ctx: int) -> tuple[float, float]:
        """Return (log P(0|ctx), log P(1|ctx))."""
        path = self._walk(ctx)
        # For each hypothetical bit b in {0, 1}, compute lpw_root_after.
        # Walk from leaf upward, computing the new lpw at each level
        # under the assumption "this is the bit we just saw".
        # Sibling child's lpw is unchanged.
        out: list[float] = [0.0, 0.0]
        for b in (0, 1):
            # At leaf: lpe_new = lpe + KT increment for b
            #          lpw_leaf_new = lpe_new (leaf has no children)
            leaf = path[DEPTH]
            lpe_new = self._lpe(leaf) + _kt_log_increment(leaf.a, leaf.b, b)
            lpw_below = lpe_new
            # Walk upward
            for d in range(DEPTH - 1, -1, -1):
                node = path[d]
                lpe_new = self._lpe(node) + _kt_log_increment(node.a, node.b, b)
                # Children: one is path[d+1] (just updated to lpw_below),
                # the other is the sibling (unchanged)
                ctx_bit = (ctx >> d) & 1
                sibling = node.right if ctx_bit == 0 else node.left
                lpw_sibling = sibling.lpw if sibling is not None else 0.0
                # CTW combine: Pw = 0.5 * Pe + 0.5 * Pw_left * Pw_right
                # log: log(0.5 * exp(lpe) + 0.5 * exp(lpw_below + lpw_sibling))
                lpw_children = lpw_below + lpw_sibling
                lpw_node = LOG_HALF + _log_add_exp(lpe_new, lpw_children)
                lpw_below = lpw_node
            out[b] = lpw_below
        # Normalize: P(b) = exp(lpw_b) / (exp(lpw_0) + exp(lpw_1))
        denom = _log_add_exp(out[0], out[1])
        return out[0] - denom, out[1] - denom

    def _lpe(self, node: CTWNode) -> float:
        """log Pe_kt at this node, computed from its (a, b) counts.
        KT estimator: Pe(seq with a 0s and b 1s) = product over n of
        (count_n + 0.5) / (n + 1) where count_n is the count of the
        seen bit before observation n."""
        a, b = node.a, node.b
        if a == 0 and b == 0:
            return 0.0
        # Sum over (a + b) observations of log((count_at_step + 0.5) / (step + 1))
        # Equivalent to: sum_{i=0}^{a-1} log((i + 0.5) / (a + b - 1 + 1)) ...
        # Simpler closed form: log Gamma(a + 0.5) + log Gamma(b + 0.5)
        #                      - 2*log Gamma(0.5) - log Gamma(a + b + 1) + log Gamma(1)
        return (
            math.lgamma(a + 0.5)
            + math.lgamma(b + 0.5)
            - 2 * math.lgamma(0.5)
            - math.lgamma(a + b + 1)
        )

    def update(self, ctx: int, bit: int) -> None:
        """Observe `bit` at this context. Update counts and lpw values
        along the path."""
        path = self._walk(ctx)
        # Update counts
        for node in path:
            if bit == 0:
                node.a += 1
            else:
                node.b += 1
        # Recompute lpw bottom-up along the path. For sibling children
        # (NOT on the path), lpw stays the same.
        # At leaf: lpw = lpe (no children)
        leaf = path[DEPTH]
        leaf.lpw = self._lpe(leaf)
        for d in range(DEPTH - 1, -1, -1):
            node = path[d]
            ctx_bit = (ctx >> d) & 1
            on_path_child = path[d + 1]
            sibling = node.right if ctx_bit == 0 else node.left
            lpw_op = on_path_child.lpw
            lpw_sib = sibling.lpw if sibling is not None else 0.0
            lpw_children = lpw_op + lpw_sib
            lpe_self = self._lpe(node)
            node.lpw = LOG_HALF + _log_add_exp(lpe_self, lpw_children)


# ─── byte-level codec via 8-bit decomposition with shared CTW tree ───

PROB_TOTAL = 1 << 14  # arithmetic coder total mass


def _quantize_log_probs(log_p0: float, log_p1: float) -> tuple[int, int, int]:
    """Convert log-probs into integer (cum_low_for_0, cum_low_for_1, total)
    suitable for the range coder. Returns (boundary, total) so that
    bit=0 occupies [0, boundary) and bit=1 occupies [boundary, total)."""
    p0 = math.exp(log_p0)
    boundary = max(1, min(PROB_TOTAL - 1, round(p0 * PROB_TOTAL)))
    return boundary, PROB_TOTAL


def pack(data: bytes) -> bytes:
    n = len(data)
    if n == 0:
        return struct.pack(">I", 0)
    ctw = BinaryCTW()
    enc = RC.RangeEncoder()
    ctx = 0  # rolling D-bit context (most recent bit in LSB)

    for byte in data:
        # MSB-first bit decomposition
        for j in range(7, -1, -1):
            bit = (byte >> j) & 1
            log_p0, log_p1 = ctw.predict_log_probs(ctx)
            boundary, total = _quantize_log_probs(log_p0, log_p1)
            if bit == 0:
                enc.encode(0, boundary, total)
            else:
                enc.encode(boundary, total, total)
            ctw.update(ctx, bit)
            ctx = ((ctx << 1) | bit) & CTX_MASK

    encoded = enc.finish()
    return struct.pack(">I", n) + encoded


def unpack(arch: bytes) -> bytes:
    (n,) = struct.unpack(">I", arch[:4])
    if n == 0:
        return b""
    payload = arch[4:]
    ctw = BinaryCTW()
    dec = RC.RangeDecoder(payload)
    ctx = 0
    out = bytearray()

    for _ in range(n):
        byte = 0
        for j in range(7, -1, -1):
            log_p0, log_p1 = ctw.predict_log_probs(ctx)
            boundary, total = _quantize_log_probs(log_p0, log_p1)
            target = dec.query(total)
            if target < boundary:
                bit = 0
                dec.update(0, boundary, total)
            else:
                bit = 1
                dec.update(boundary, total, total)
            byte = (byte << 1) | bit
            ctw.update(ctx, bit)
            ctx = ((ctx << 1) | bit) & CTX_MASK
        out.append(byte)

    return bytes(out)
