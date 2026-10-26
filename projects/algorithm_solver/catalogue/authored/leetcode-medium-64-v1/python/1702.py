"""1702. Maximum Binary String After Change: place the sole remaining zero after the leading ones and absorbed zeros."""


def solve(binary: str) -> str:
    """O(n) time and O(n) output-construction space; inputs are read-only."""
    zeros = binary.count('0')
    if zeros <= 1:
        return binary
    position = binary.find('0') + zeros - 1
    return '1' * position + '0' + '1' * (len(binary) - position - 1)


class Solution:
    def maximumBinaryString(self, binary: str) -> str:
        return solve(binary)
