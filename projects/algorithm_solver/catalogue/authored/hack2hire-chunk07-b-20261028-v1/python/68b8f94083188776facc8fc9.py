"""Hack2Hire 68b8f94083188776facc8fc9 (Minimum Menu Order Cost II) over an INFERRED spec; qualification unknown."""

def solve(menu, userWants):
    index = {x: i for i, x in enumerate(userWants)}
    w = len(userWants)
    full = (1 << w) - 1
    containing = [[] for _ in range(w)]
    for entry_id, price, items in menu:
        parts = items.split(',')
        if all(x in index for x in parts):
            mask = 0
            for x in parts:
                mask |= 1 << index[x]
            for bit in range(w):
                if mask >> bit & 1:
                    containing[bit].append((mask, price, entry_id))
    best = [None] * (full + 1)
    best[0] = 0
    for rem in range(1, full + 1):
        low = (rem & -rem).bit_length() - 1
        for mask, price, _ in containing[low]:
            if mask & ~rem == 0 and best[rem ^ mask] is not None:
                c = price + best[rem ^ mask]
                if best[rem] is None or c < best[rem]:
                    best[rem] = c
    if best[full] is None:
        return []
    found = []

    def walk(rem, chosen):
        if rem == 0:
            found.append(sorted(chosen))
            return
        low = (rem & -rem).bit_length() - 1
        for mask, price, entry_id in containing[low]:
            if mask & ~rem == 0 and best[rem ^ mask] is not None and price + best[rem ^ mask] == best[rem]:
                chosen.append(entry_id)
                walk(rem ^ mask, chosen)
                chosen.pop()

    walk(full, [])
    found.sort()
    return found


class Solution:
    def cheapestExactOrders(self, menu, userWants):
        return solve(menu, userWants)
