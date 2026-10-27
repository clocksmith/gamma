"""228. Summary Ranges."""
def solve(nums: list[int]) -> list[str]:
    result = []
    start = 0
    while start < len(nums):
        end = start
        while end + 1 < len(nums) and nums[end + 1] == nums[end] + 1:
            end += 1
        result.append(str(nums[start]) if start == end else f'{nums[start]}->{nums[end]}')
        start = end + 1
    return result

class Solution:
    def summaryRanges(self, nums: list[int]) -> list[str]:
        return solve(nums)
