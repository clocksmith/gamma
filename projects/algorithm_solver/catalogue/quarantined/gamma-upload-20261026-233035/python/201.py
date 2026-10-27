"""201. Bitwise AND of Numbers Range."""
def solve(left: int, right: int) -> int:
    shifts = 0
    while left < right:
        left >>= 1
        right >>= 1
        shifts += 1
    return left << shifts

class Solution:
    def rangeBitwiseAnd(self, left: int, right: int) -> int:
        return solve(left, right)
