"""3031. Minimum Time to Revert Word to Initial State II.

Z-function checks every possible retained suffix; O(n) time and space.
"""

def solve(word: str, k: int) -> int:
    n = len(word)
    z = [0] * n
    left = right = 0
    for index in range(1, n):
        if index <= right:
            z[index] = min(right - index + 1, z[index - left])
        while index + z[index] < n and word[z[index]] == word[index + z[index]]:
            z[index] += 1
        if index + z[index] - 1 > right:
            left, right = index, index + z[index] - 1
    for removed in range(k, n, k):
        if z[removed] >= n - removed:
            return removed // k
    return (n + k - 1) // k


class Solution:
    def minimumTimeToInitialState(self, word: str, k: int) -> int:
        return solve(word, k)
