"""351. Android Unlock Patterns."""
def solve(m: int, n: int) -> int:
    skip = [[0] * 10 for _ in range(10)]
    for left, right, middle in ((1, 3, 2), (1, 7, 4), (3, 9, 6), (7, 9, 8),
                                (1, 9, 5), (3, 7, 5), (2, 8, 5), (4, 6, 5)):
        skip[left][right] = skip[right][left] = middle
    used = [False] * 10
    def visit(current: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        used[current] = True
        total = 0
        for following in range(1, 10):
            middle = skip[current][following]
            if not used[following] and (middle == 0 or used[middle]):
                total += visit(following, remaining - 1)
        used[current] = False
        return total
    total = 0
    for length in range(m, n + 1):
        total += visit(1, length - 1) * 4
        total += visit(2, length - 1) * 4
        total += visit(5, length - 1)
    return total

class Solution:
    def numberOfPatterns(self, m: int, n: int) -> int:
        return solve(m, n)
