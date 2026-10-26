"""2100. Find Good Days to Rob the Bank: combine the nonincreasing prefix run and nondecreasing suffix run at each day."""


def solve(security: list[int], time: int) -> list[int]:
    """O(n) time and O(n) auxiliary and result space; inputs are read-only."""
    size = len(security)
    before = [0] * size
    after = [0] * size
    for index in range(1, size):
        if security[index] <= security[index - 1]:
            before[index] = before[index - 1] + 1
    for index in range(size - 2, -1, -1):
        if security[index] <= security[index + 1]:
            after[index] = after[index + 1] + 1
    return [index for index in range(size) if before[index] >= time and after[index] >= time]


class Solution:
    def goodDaysToRobBank(self, security: list[int], time: int) -> list[int]:
        return solve(security, time)
