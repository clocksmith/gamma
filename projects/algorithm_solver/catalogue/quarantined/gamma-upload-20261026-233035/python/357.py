"""357. Count Numbers with Unique Digits."""
def solve(n: int) -> int:
    if n == 0:
        return 1
    total = 10
    current = 9
    available = 9
    for _ in range(2, min(n, 10) + 1):
        current *= available
        total += current
        available -= 1
    return total

class Solution:
    def countNumbersWithUniqueDigits(self, n: int) -> int:
        return solve(n)
