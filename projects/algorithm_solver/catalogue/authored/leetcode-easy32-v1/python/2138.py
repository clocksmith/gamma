"""2138. Divide a String Into Groups of Size k (Easy).

Specification: https://leetcode.com/problems/divide-a-string-into-groups-of-size-k/description/
"""


def solve(s: str, k: int, fill: str) -> list[str]:
    """O(n + k) time and output space; pad only the final partial group."""
    result = []
    for start in range(0, len(s), k):
        group = s[start:start + k]
        result.append(group + fill * (k - len(group)))
    return result


class Solution:
    def divideString(self, s: str, k: int, fill: str) -> list[str]:
        return solve(s, k, fill)
