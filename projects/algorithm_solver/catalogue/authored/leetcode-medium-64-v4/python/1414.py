"""1414. Find the Minimum Number of Fibonacci Numbers Whose Sum Is K: subtract the largest usable Fibonacci number at each step."""


def solve(k: int) -> int:
    """O(log(k + 1)) time and O(log(k + 1)) auxiliary space; inputs are read-only."""
    fibonacci = [1, 2]
    while fibonacci[-1] < k:
        fibonacci.append(fibonacci[-1] + fibonacci[-2])
    remaining = k
    count = 0
    for value in reversed(fibonacci):
        if value <= remaining:
            remaining -= value
            count += 1
    return count


class Solution:
    def findMinFibonacciNumbers(self, k: int) -> int:
        return solve(k)
