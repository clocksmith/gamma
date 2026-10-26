"""942. DI String Match (Easy).

Specification: https://leetcode.com/problems/di-string-match/description/
"""


def solve(s: str) -> list[int]:
    """O(n) time and space; choose the smallest unused value for I and largest for D."""
    smallest, largest = 0, len(s)
    result = []
    for direction in s:
        if direction == 'I':
            result.append(smallest)
            smallest += 1
        else:
            result.append(largest)
            largest -= 1
    result.append(smallest)
    return result


class Solution:
    def diStringMatch(self, s: str) -> list[int]:
        return solve(s)
