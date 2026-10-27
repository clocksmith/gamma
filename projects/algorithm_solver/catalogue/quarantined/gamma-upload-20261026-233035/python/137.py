"""137. Single Number II."""
def solve(nums: list[int]) -> int:
    result = 0
    for bit in range(32):
        if sum((value >> bit) & 1 for value in nums) % 3:
            result |= 1 << bit
    return result - (1 << 32) if result >= 1 << 31 else result

class Solution:
    def singleNumber(self, nums: list[int]) -> int:
        return solve(nums)
