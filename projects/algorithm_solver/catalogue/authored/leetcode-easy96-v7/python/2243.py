"""2243. Calculate Digit Sum of a String (Easy).

Specification: https://leetcode.com/problems/calculate-digit-sum-of-a-string/description/
"""


def solve(s: str, k: int) -> str:
    """O(n) total time and O(n) space for k >= 2; sum consecutive groups until at most k digits remain."""
    current = s
    while len(current) > k:
        groups = []
        for start in range(0, len(current), k):
            total = 0
            for index in range(start, min(start + k, len(current))):
                total += ord(current[index]) - 48
            groups.append(str(total))
        current = ''.join(groups)
    return current


class Solution:
    def digitSum(self, s: str, k: int) -> str:
        return solve(s, k)
