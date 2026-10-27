"""260. Single Number III."""
def solve(nums: list[int]) -> list[int]:
    combined = 0
    for value in nums:
        combined ^= value
    bit = combined & -combined
    first = 0
    for value in nums:
        if value & bit:
            first ^= value
    return [first, combined ^ first]

class Solution:
    def singleNumber(self, nums: list[int]) -> list[int]:
        return solve(nums)
