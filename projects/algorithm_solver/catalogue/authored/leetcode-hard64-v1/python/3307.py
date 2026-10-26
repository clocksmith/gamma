"""3307. Find the K-th Character in String Game II: read the doubling ancestry from the bits of k minus one."""


def solve(k: int, operations: list[int]) -> str:
    """O(log k) time and O(1) auxiliary space. Inputs are preserved."""
    position = k - 1
    shift = 0
    index = 0
    while position:
        if position & 1:
            shift = (shift + operations[index]) % 26
        position >>= 1
        index += 1
    return chr(ord('a') + shift)


class Solution:
    def kthCharacter(self, k: int, operations: list[int]) -> str:
        return solve(k, operations)
