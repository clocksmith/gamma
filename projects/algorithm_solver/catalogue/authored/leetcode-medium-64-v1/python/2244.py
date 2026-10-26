"""2244. Minimum Rounds to Complete All Tasks: group each frequency into triples with pairs for the remainder."""


def solve(tasks: list[int]) -> int:
    """O(n) expected time and O(u) auxiliary space for u distinct difficulties; inputs are read-only."""
    counts = {}
    for task in tasks:
        counts[task] = counts.get(task, 0) + 1
    answer = 0
    for count in counts.values():
        if count == 1:
            return -1
        answer += (count + 2) // 3
    return answer


class Solution:
    def minimumRounds(self, tasks: list[int]) -> int:
        return solve(tasks)
