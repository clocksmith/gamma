"""1256. Encode Number: remove the leading one from the binary representation of the successor."""


def solve(num: int) -> str:
    """O(log(num + 2)) time and output space; inputs are read-only."""
    return bin(num + 1)[3:]


class Solution:
    def encode(self, num: int) -> str:
        return solve(num)
