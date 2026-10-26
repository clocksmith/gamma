"""2747. Count Zero Request Servers: answer sorted queries with an inclusive sliding time window of active servers."""


def solve(n: int, logs: list[list[int]], x: int, queries: list[int]) -> list[int]:
    """O(l log l + q log q + n) time and O(l + q + n) auxiliary space; inputs are read-only."""
    ordered_logs = sorted(logs, key=lambda row: row[1])
    order = sorted(range(len(queries)), key=lambda index: queries[index])
    counts = [0] * (n + 1)
    result = [0] * len(queries)
    left = right = active = 0
    for index in order:
        time = queries[index]
        while right < len(ordered_logs) and ordered_logs[right][1] <= time:
            server = ordered_logs[right][0]
            if counts[server] == 0:
                active += 1
            counts[server] += 1
            right += 1
        while left < right and ordered_logs[left][1] < time - x:
            server = ordered_logs[left][0]
            counts[server] -= 1
            if counts[server] == 0:
                active -= 1
            left += 1
        result[index] = n - active
    return result


class Solution:
    def countServers(self, n: int, logs: list[list[int]], x: int, queries: list[int]) -> list[int]:
        return solve(n, logs, x, queries)
