"""1817. Finding the Users Active Minutes: deduplicate minutes per user and count activity totals."""


def solve(logs: list[list[int]], k: int) -> list[int]:
    """O(n + k) expected time and O(n) auxiliary space excluding the result; inputs are read-only."""
    minutes_by_user = {}
    for user, minute in logs:
        minutes_by_user.setdefault(user, set()).add(minute)
    answer = [0] * k
    for minutes in minutes_by_user.values():
        answer[len(minutes) - 1] += 1
    return answer


class Solution:
    def findingUsersActiveMinutes(self, logs: list[list[int]], k: int) -> list[int]:
        return solve(logs, k)
