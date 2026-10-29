"""Hack2Hire 687e65b7eab243475a7dfbf7 (Find Frequent Events in 24 Hours) over an INFERRED spec; qualification unknown."""


def solve(logs, k):
    groups = {}
    for user, stamp, event in logs:
        key = (user, event)
        times = groups.get(key)
        if times is None:
            times = []
            groups[key] = times
        times.append(stamp)
    found = set()
    for (_, event), times in groups.items():
        if event in found or len(times) < k:
            continue
        times.sort()
        for i in range(len(times) - k + 1):
            if times[i + k - 1] - times[i] < 86400:
                found.add(event)
                break
    return sorted(found)


class Solution:
    def findFrequentEvents(self, logs, k):
        return solve(logs, k)
