"""3193. Count the Number of Inversions.

Prefix inversion DP with a sliding transition sum and immediate constraint filtering; O(n*C) time and O(C) space. Inputs are preserved.
"""

def solve(n: int, requirements: list[list[int]]) -> int:
    modulus = 1_000_000_007
    required = dict(requirements)
    cap = max(required.values(), default=n * (n - 1) // 2)
    if any(count > (end + 1) * end // 2 for end, count in requirements):
        return 0
    ways = [1] + [0] * cap
    for length in range(1, n + 1):
        following = [0] * (cap + 1)
        window = 0
        for inversions in range(cap + 1):
            window += ways[inversions]
            if inversions >= length:
                window -= ways[inversions - length]
            window %= modulus
            following[inversions] = window
        if length - 1 in required:
            wanted = required[length - 1]
            retained = following[wanted]
            following = [0] * (cap + 1)
            following[wanted] = retained
        ways = following
    return sum(ways) % modulus


class Solution:
    def numberOfPermutations(self, n: int, requirements: list[list[int]]) -> int:
        return solve(n, requirements)
