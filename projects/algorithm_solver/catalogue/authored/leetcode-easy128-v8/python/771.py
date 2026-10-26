"""771. Jewels and Stones (Easy).

Specification: https://leetcode.com/problems/jewels-and-stones/description/
"""


def solve(jewels: str, stones: str) -> int:
    """O(j + s) expected time, O(j) space; distinguish uppercase and lowercase letters."""
    valuable = set(jewels)
    result = 0
    for stone in stones:
        if stone in valuable:
            result += 1
    return result


class Solution:
    def numJewelsInStones(self, jewels: str, stones: str) -> int:
        return solve(jewels, stones)
