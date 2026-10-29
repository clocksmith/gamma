"""Hack2Hire 6acd8f922e3a0349b3a8d6fc (Transaction Incident Monitor, level 1) over an INFERRED spec; qualification unknown."""

from collections import deque

LEVEL = 1


def solve(logs, windowSize, *limits):
    by_merchant = {}
    for line in logs:
        t, merchant, code, count = line.split(',')
        by_merchant.setdefault(merchant, []).append((int(t), int(code), int(count)))
    alerts = []
    for merchant, records in by_merchant.items():
        records.sort(key=lambda r: r[0])
        window, counts, total, active, fired = deque(), {}, 0, set(), set()
        i = 0
        while i < len(records):
            t = records[i][0]
            arrived = set()
            while i < len(records) and records[i][0] == t:
                rec = records[i]
                window.append(rec)
                if rec[2]:
                    counts[rec[1]] = counts.get(rec[1], 0) + rec[2]
                total += rec[2]
                arrived.add(rec[1])
                i += 1
            while window[0][0] < t - windowSize + 1:
                old = window.popleft()
                if not old[2]:
                    continue
                left = counts[old[1]] - old[2]
                total -= old[2]
                if left == 0:
                    del counts[old[1]]
                else:
                    counts[old[1]] = left
            if LEVEL == 1:
                codes = arrived
            elif LEVEL == 2:
                codes = list(counts)
            else:
                codes = set(counts) | active
            for code in codes:
                if code == 200:
                    continue
                c = counts.get(code, 0)
                if LEVEL == 1:
                    ok = c >= limits[0]
                else:
                    ok = c >= limits[0] and c * 100 >= limits[1] * total
                if LEVEL == 3:
                    if ok and code not in active:
                        active.add(code)
                        alerts.append((t, merchant, code))
                    elif not ok:
                        active.discard(code)
                elif ok and code not in fired:
                    fired.add(code)
                    alerts.append((t, merchant, code))
    alerts.sort()
    return ['%d,%s,%d' % alert for alert in alerts]


class Solution:
    def detectIncidents(self, logs, windowSize, threshold):
        return solve(logs, windowSize, threshold)
