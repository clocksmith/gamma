"""Original frontend 3784 development variant; qualification unknown."""

def solve(s, cost):
    saved = [0] * 26
    for char, value in zip(s, cost):
        saved[ord(char) - 97] += value
    return sum(cost) - max(saved)


class Solution:
    def minCost(self, s, cost):
        return solve(s, cost)
