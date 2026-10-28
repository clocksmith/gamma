"""473. Matchsticks to Square (Medium).

Specification: https://leetcode.com/problems/matchsticks-to-square/description/
"""


def solve(matchsticks: list[int]) -> bool:
    total = sum(matchsticks)
    if total % 4 != 0:
        return False
    target = total // 4
    ordered = sorted(matchsticks, reverse=True)
    sides = [0, 0, 0, 0]

    def backtrack(index):
        if index == len(ordered):
            return all(side == target for side in sides)
        for side in range(4):
            if sides[side] + ordered[index] > target:
                continue
            sides[side] += ordered[index]
            if backtrack(index + 1):
                return True
            sides[side] -= ordered[index]
            if sides[side] == 0:
                break
        return False

    return backtrack(0)


class Solution:
    def makesquare(self, matchsticks: list[int]) -> bool:
        return solve(matchsticks)
