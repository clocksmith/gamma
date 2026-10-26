"""1604. Alert Using Same Key-Card Three or More Times in a One Hour Period: sort each person's same-day uses and inspect consecutive triples."""


def solve(keyName: list[str], keyTime: list[str]) -> list[str]:
    """O(n log(n + 1)) time and O(n) auxiliary space on the bounded name domain; inputs are read-only."""
    uses = {}
    for name, time in zip(keyName, keyTime):
        minute = int(time[:2]) * 60 + int(time[3:])
        uses.setdefault(name, []).append(minute)
    result = []
    for name, times in uses.items():
        times.sort()
        if any(times[index] - times[index - 2] <= 60 for index in range(2, len(times))):
            result.append(name)
    return sorted(result)


class Solution:
    def alertNames(self, keyName: list[str], keyTime: list[str]) -> list[str]:
        return solve(keyName, keyTime)
