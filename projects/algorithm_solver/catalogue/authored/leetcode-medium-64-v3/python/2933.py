"""2933. High-Access Employees: find three sorted same-day accesses less than sixty minutes apart."""


def solve(access_times: list[list[str]]) -> list[str]:
    """O(n log n) time and O(n) auxiliary space for bounded-length employee names; inputs are read-only."""
    times = {}
    for name, clock in access_times:
        minute = int(clock[:2]) * 60 + int(clock[2:])
        times.setdefault(name, []).append(minute)
    result = []
    for name, visits in times.items():
        visits.sort()
        if any(visits[index] - visits[index - 2] < 60 for index in range(2, len(visits))):
            result.append(name)
    return sorted(result)


class Solution:
    def findHighAccessEmployees(self, access_times: list[list[str]]) -> list[str]:
        return solve(access_times)
