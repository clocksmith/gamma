"""3363. Find the Maximum Number of Fruits Collected: forced diagonal plus independent optimal paths above and below it."""


def solve(fruits: list[list[int]]) -> int:
    """O(n^2) time and O(n) auxiliary space for nonnegative fruit counts. Inputs are preserved."""
    n = len(fruits)
    if n == 1:
        return fruits[0][0]
    answer = sum(fruits[index][index] for index in range(n))

    def side(transposed):
        previous = [float('-inf')] * n
        previous[n - 1] = fruits[n - 1][0] if transposed else fruits[0][n - 1]
        for step in range(1, n - 1):
            following = [float('-inf')] * n
            for position in range(step + 1, n):
                best = previous[position]
                if position > 0:
                    best = max(best, previous[position - 1])
                if position + 1 < n:
                    best = max(best, previous[position + 1])
                value = fruits[position][step] if transposed else fruits[step][position]
                following[position] = best + value
            previous = following
        return previous[n - 1]

    return int(answer + side(False) + side(True))


class Solution:
    def maxCollectedFruits(self, fruits: list[list[int]]) -> int:
        return solve(fruits)
