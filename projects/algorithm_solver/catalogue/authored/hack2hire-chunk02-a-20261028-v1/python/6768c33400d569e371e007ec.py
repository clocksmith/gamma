"""Hack2Hire 6768c33400d569e371e007ec (High Correlation Seller); INFERRED spec; qualification unknown."""


def solve(records):
    pairs, stores = {}, set()
    for record in records:
        session = sorted(set(record))
        stores.update(session)
        for i, a in enumerate(session):
            row = pairs.setdefault(a, {})
            for b in session[i + 1:]:
                row[b] = row.get(b, 0) + 1
                other = pairs.setdefault(b, {}); other[a] = other.get(a, 0) + 1
    out = []
    for store in sorted(stores):
        row = pairs.get(store, {})
        best = max(row.values(), default=0)
        out.append([store, sorted(s for s, c in row.items() if c == best and best > 0)])
    return out


class Solution:
    def highCorrelationSellers(self, records):
        return solve(records)
