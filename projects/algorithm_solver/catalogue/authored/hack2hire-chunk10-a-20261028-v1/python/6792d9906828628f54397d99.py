"""Hack2Hire 6792d9906828628f54397d99 (Design Query Pagination) over an INFERRED spec; qualification unknown."""


def _cents(amount):
    whole, _, frac = amount.partition('.')
    return int(whole) * 100 + int((frac + '00')[:2])


def solve(records, filters, pageSize, pageNumber):
    lo_t, hi_t, lo_a, hi_a, user, currency = filters
    lo_t = int(lo_t) if lo_t else None
    hi_t = int(hi_t) if hi_t else None
    lo_a = _cents(lo_a) if lo_a else None
    hi_a = _cents(hi_a) if hi_a else None
    hits = []
    for r in records:
        t = int(r[0])
        if (lo_t is not None and t < lo_t) or (hi_t is not None and t > hi_t):
            continue
        if (user and r[2] != user) or (currency and r[3] != currency):
            continue
        if lo_a is not None or hi_a is not None:
            a = _cents(r[4])
            if (lo_a is not None and a < lo_a) or (hi_a is not None and a > hi_a):
                continue
        hits.append((t, r))
    hits.sort(key=lambda h: h[0])  # stable: equal timestamps keep input order
    start = (pageNumber - 1) * pageSize
    return [list(r) for _, r in hits[start:start + pageSize]]


class Solution:
    def queryTransactions(self, records, filters, pageSize, pageNumber):
        return solve(records, filters, pageSize, pageNumber)
