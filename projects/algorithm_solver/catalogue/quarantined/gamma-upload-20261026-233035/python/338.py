"""338. Counting Bits."""
def solve(n: int) -> list[int]:
    result = [0] * (n + 1)
    for value in range(1, n + 1):
        result[value] = result[value >> 1] + (value & 1)
    return result

class Solution:
    def countBits(self, n: int) -> list[int]:
        return solve(n)
