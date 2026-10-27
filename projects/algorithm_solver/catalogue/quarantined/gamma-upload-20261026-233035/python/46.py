"""46. Permutations."""
def solve(nums: list[int]) -> list[list[int]]:
    result = []
    def visit(index: int) -> None:
        if index == len(nums):
            result.append(nums.copy())
            return
        for swap in range(index, len(nums)):
            nums[index], nums[swap] = nums[swap], nums[index]
            visit(index + 1)
            nums[index], nums[swap] = nums[swap], nums[index]
    visit(0)
    return result

class Solution:
    def permute(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
