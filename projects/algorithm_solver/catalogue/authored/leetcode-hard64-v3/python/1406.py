"""1406. Stone Game III: suffix score-difference DP; O(n) time and O(n) space. Inputs are preserved."""


def solve(stoneValue: list[int]) -> str:
    size = len(stoneValue)
    difference = [0] * (size + 1)
    for index in range(size - 1, -1, -1):
        total = 0
        best = float('-inf')
        for end in range(index, min(size, index + 3)):
            total += stoneValue[end]
            best = max(best, total - difference[end + 1])
        difference[index] = best
    if difference[0] > 0:
        return 'Alice'
    if difference[0] < 0:
        return 'Bob'
    return 'Tie'


class Solution:
    def stoneGameIII(self, stoneValue: list[int]) -> str:
        return solve(stoneValue)
