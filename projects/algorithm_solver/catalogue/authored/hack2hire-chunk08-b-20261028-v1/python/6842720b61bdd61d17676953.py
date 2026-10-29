"""Hack2Hire 6842720b61bdd61d17676953 (Spam Caller Counter) over an INFERRED spec; qualification unknown."""

from bisect import bisect_left, bisect_right


def _days_from_civil(y, m, d):
    y -= m <= 2
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def _seconds(ts, cache):
    value = cache.get(ts)
    if value is None:
        value = (_days_from_civil(int(ts[0:4]), int(ts[5:7]), int(ts[8:10])) * 86400
                 + int(ts[11:13]) * 3600 + int(ts[14:16]) * 60 + int(ts[17:19]))
        cache[ts] = value
    return value


def solve(calls, reports, window):
    cache = {}
    by_receiver = {}
    for receiver, ts in reports:
        by_receiver.setdefault(receiver, []).append(_seconds(ts, cache))
    for times in by_receiver.values():
        times.sort()
    totals = {}
    for caller, receiver, ts in calls:
        times = by_receiver.get(receiver)
        if times:
            t = _seconds(ts, cache)
            count = bisect_right(times, t + window) - bisect_left(times, t - window)
            if count:
                totals[caller] = totals.get(caller, 0) + count
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return [[caller, count] for caller, count in ranked]


class Solution:
    def countSpamCalls(self, calls, reports, window):
        return solve(calls, reports, window)
