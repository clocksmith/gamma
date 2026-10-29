"""Original LeetCode 629 candidate; qualification unknown."""

def solve(n, k):
    mod = 1000000007
    previous = [1] + [0] * k
    for length in range(1, n + 1):
        current, window = [0] * (k + 1), 0
        for inv in range(k + 1):
            window += previous[inv]
            if inv >= length:
                window -= previous[inv - length]
            window %= mod
            current[inv] = window
        previous = current
    return previous[k]


class Solution:
    def kInversePairs(self, n, k):
        return solve(n, k)
