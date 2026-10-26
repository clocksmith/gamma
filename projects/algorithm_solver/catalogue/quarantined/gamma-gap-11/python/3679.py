"""3679. Minimum Discards to Balance Inventory."""
from __future__ import annotations


def solve(arrivals: list[int], w: int, m: int) -> int:
    """O(n) expected time and O(w) auxiliary space; inputs are preserved."""
    counts = {}
    kept = [False] * w
    answer = 0
    for day, item in enumerate(arrivals):
        slot = day % w
        if day >= w and kept[slot]:
            old = arrivals[day - w]
            counts[old] -= 1
            if counts[old] == 0:
                del counts[old]
        if counts.get(item, 0) == m:
            kept[slot] = False
            answer += 1
        else:
            kept[slot] = True
            counts[item] = counts.get(item, 0) + 1
    return answer


class Solution:
    def minArrivalsToDiscard(self, arrivals: list[int], w: int, m: int) -> int:
        return solve(arrivals, w, m)
