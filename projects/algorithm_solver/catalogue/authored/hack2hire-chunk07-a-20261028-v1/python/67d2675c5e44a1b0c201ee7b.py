"""Hack2Hire 67d2675c5e44a1b0c201ee7b (Margin Call, level 3) over an INFERRED spec; qualification unknown."""

import heapq

LEVEL = 3


def solve(trades):
    cash, held, price, heap = 1000, {}, {}, []

    def sellable(sym):
        q = held.get(sym, 0)
        if LEVEL < 3 or sym.endswith('O'):
            return q
        return max(0, q - held.get(sym + 'O', 0))

    def push(sym):
        if sym in price:
            heapq.heappush(heap, (-price[sym], sym))

    def change(sym, delta):
        q = held.get(sym, 0) + delta
        if q:
            held[sym] = q
        else:
            held.pop(sym, None)

    def margin_call(cash):
        while cash < 0:
            while heap and (price[heap[0][1]] != -heap[0][0] or sellable(heap[0][1]) == 0):
                heapq.heappop(heap)
            if not heap:
                break
            sym = heap[0][1]
            p, deficit = price[sym], -cash
            base = sym[:-1] if LEVEL == 3 and sym.endswith('O') else None
            if base is not None and base in held and price[base] >= p:
                # the stock is better but locked: options alone until the counts match, then option/stock pairs
                pb, qx, qu = price[base], held[sym], held[base]
                n = min(max(0, qx - qu), (deficit + p - 1) // p)
                cash += n * p
                change(sym, -n)
                qx -= n
                if cash < 0 and qx:
                    pairs = (-cash - 1) // (p + pb)
                    if pairs >= qx:
                        cash += qx * (p + pb)
                        change(sym, -qx)
                        change(base, -qx)
                    else:
                        cash += pairs * (p + pb) + p
                        change(sym, -pairs - 1)
                        change(base, -pairs)
                        if cash < 0:
                            cash += pb
                            change(base, -1)
                push(base)
            else:
                n = min(sellable(sym), (deficit + p - 1) // p)
                cash += n * p
                change(sym, -n)
                if base is not None:
                    push(base)
        return cash

    for _, sym, direction, quantity, unit in trades:
        q, p = int(quantity), int(unit)
        price[sym] = p
        if direction == 'B':
            cash -= q * p
            change(sym, q)
        else:
            q = min(q, held.get(sym, 0))
            cash += q * p
            change(sym, -q)
        if LEVEL >= 2:
            push(sym)
            if LEVEL == 3 and sym.endswith('O'):
                push(sym[:-1])
            if cash < 0:
                cash = margin_call(cash)
    return [['CASH', str(cash)]] + [[sym, str(held[sym])] for sym in sorted(held)]


class Solution:
    def marginCall(self, trades):
        return solve(trades)
