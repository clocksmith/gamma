"""Hack2Hire 69752cb217272b5c868d5e84 (Schedule Orders onto Planes) over an INFERRED spec; qualification unknown."""

from bisect import bisect_right


def solve(planes, orders):
    fleet = sorted((p[0], p[1]) for p in planes)
    departures = [d for d, _ in fleet]
    count = len(fleet)
    size = 1
    while size < count:
        size *= 2
    tree = [-1] * (2 * size)
    for i, (_, capacity) in enumerate(fleet):
        tree[size + i] = capacity
    for node in range(size - 1, 0, -1):
        tree[node] = max(tree[2 * node], tree[2 * node + 1])

    def update(i, value):
        node = size + i
        tree[node] = value
        node //= 2
        while node:
            tree[node] = max(tree[2 * node], tree[2 * node + 1])
            node //= 2

    def first(node, lo, hi, start, need):
        # leftmost leaf index >= start in [lo, hi) holding at least need, or -1
        if hi <= start or tree[node] < need:
            return -1
        if hi - lo == 1:
            return lo
        mid = (lo + hi) // 2
        found = first(2 * node, lo, mid, start, need)
        return found if found != -1 else first(2 * node + 1, mid, hi, start, need)

    out = []
    for ship_time, items in orders:
        start = bisect_right(departures, ship_time)
        log, chosen = [], []
        for item in items:
            i = first(1, 0, size, start, item)
            if i == -1:
                for j, old in reversed(log):
                    update(j, old)
                chosen = []
                break
            log.append((i, tree[size + i]))
            update(i, tree[size + i] - item)
            chosen.append(departures[i])
        out.append(chosen)
    return out


class Solution:
    def scheduleOrders(self, planes, orders):
        return solve(planes, orders)
