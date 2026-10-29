"""Hack2Hire 69a3c6546e73e4abccc9c150 (Shard Rebalancing) over an INFERRED spec; qualification unknown."""

from bisect import bisect_left, bisect_right, insort


def solve(limit, shards):
    parsed = []
    for shard in shards:
        ident, start, end = shard.split(':')
        parsed.append((int(start), int(end), ident))
    parsed.sort()
    starts, ends, kept = [], [], []

    def coverage(x):
        return bisect_right(starts, x) - bisect_left(ends, x)

    for start, end, ident in parsed:
        base = bisect_left(ends, start)

        def candidate(t):
            return start if t == 0 else ends[base + t - 1] + 1
        lo, hi = 0, len(ends) - base
        while lo < hi:  # coverage is non-increasing from start, so the first point under the limit is found by bisection
            mid = (lo + hi) // 2
            if coverage(candidate(mid)) < limit:
                hi = mid
            else:
                lo = mid + 1
        new_start = candidate(lo)
        if new_start <= end:
            insort(starts, new_start)
            insort(ends, end)
            kept.append([new_start, end, ident])
    kept.sort(key=lambda k: (k[0], k[1], k[2]))
    reach = None
    for shard in kept:
        if reach is not None and shard[0] > reach + 1:
            shard[0] = reach + 1
        reach = shard[1] if reach is None else max(reach, shard[1])
    kept.sort(key=lambda k: (k[0], k[1], k[2]))
    return ['%s:%d:%d' % (ident, start, end) for start, end, ident in kept]


class Solution:
    def rebalance(self, limit, shards):
        return solve(limit, shards)
