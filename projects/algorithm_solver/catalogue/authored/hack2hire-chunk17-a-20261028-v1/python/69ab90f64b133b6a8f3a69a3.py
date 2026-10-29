"""Hack2Hire 69ab90f64b133b6a8f3a69a3 (Thread Logs Processing, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(logs):
    stats = {}  # (processId, threadId) -> [count, first, last]
    for entry in logs:
        process, thread, stamp, _ = entry.split(':', 3)
        t = int(stamp)
        row = stats.get((process, thread))
        if row is None:
            stats[(process, thread)] = [1, t, t]
        else:
            row[0] += 1
            if t < row[1]:
                row[1] = t
            if t > row[2]:
                row[2] = t
    return ['%s:%s:%d:%d:%d' % (p, q, *stats[(p, q)]) for p, q in sorted(stats)]


class Solution:
    def summarizeThreads(self, logs):
        return solve(logs)
