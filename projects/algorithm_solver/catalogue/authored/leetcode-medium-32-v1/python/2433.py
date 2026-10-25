"""2433. Find The Original Array of Prefix Xor: cancel adjacent prefix XOR values."""


def solve(pref: list[int]) -> list[int]:
    """O(n) time and O(1) auxiliary space excluding the result; inputs are read-only."""
    answer = []
    previous = 0
    for value in pref:
        answer.append(previous ^ value)
        previous = value
    return answer


class Solution:
    def findArray(self, pref: list[int]) -> list[int]:
        return solve(pref)
