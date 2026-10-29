"""Hack2Hire 68c331ec1f64f4312b0a3e2d (Subscription Billing Statement) over an INFERRED spec; qualification unknown."""


def _leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def solve(plans, events):
    if not events:
        return []
    price = {name: cents for name, cents in plans}
    year = int(events[0][0][:4])
    lengths = [31, 29 if _leap(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    firsts = [1]
    for length in lengths[:-1]:
        firsts.append(firsts[-1] + length)
    year_end = firsts[-1] + lengths[-1]

    def day_of_year(date):
        return firsts[int(date[5:7]) - 1] + int(date[8:10]) - 1

    intervals = []
    active, since = None, 0
    for date, kind, name in events:
        day = day_of_year(date)
        if active is not None:
            intervals.append((since, day, active))
        active, since = (None if kind == 'END' else name), day
    if active is not None:
        intervals.append((since, year_end, active))
    numerators = [0] * 12
    billed = [0] * 12
    for lo, hi, name in intervals:
        for month in range(12):
            overlap = min(hi, firsts[month] + lengths[month]) - max(lo, firsts[month])
            if overlap > 0:
                numerators[month] += price[name] * overlap
                billed[month] += overlap
    out = []
    for month in range(12):
        if billed[month]:
            days = lengths[month]
            out.append(['%04d-%02d' % (year, month + 1), (2 * numerators[month] + days) // (2 * days)])
    return out


class Solution:
    def billingStatement(self, plans, events):
        return solve(plans, events)
