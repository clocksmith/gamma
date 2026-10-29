"""Hack2Hire 68f68778a269f53ea0eff91d (Product Price Query System) over an INFERRED spec; qualification unknown."""

from bisect import bisect_right


def solve(log, queries):
    history = {}
    for entry in log:
        item, date, price = entry.rsplit(', ', 2)
        history.setdefault(item, []).append((date, int(price)))
    index = {}
    for item, rows in history.items():
        rows = sorted(rows)
        index[item] = ([d for d, _ in rows], [p for _, p in rows])
    out = []
    for item, date in queries:
        found = index.get(item)
        if found is None:
            out.append(-1)
            continue
        k = bisect_right(found[0], date)
        out.append(found[1][k - 1] if k else -1)
    return out


class Solution:
    def getPrices(self, log, queries):
        return solve(log, queries)
