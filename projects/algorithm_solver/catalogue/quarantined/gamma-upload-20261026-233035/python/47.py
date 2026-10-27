"""47. Permutations II."""
def solve(nums: list[int]) -> list[list[int]]:
    nums = sorted(nums)
    used = [False] * len(nums)
    result = []
    path = []
    def visit() -> None:
        if len(path) == len(nums):
            result.append(path.copy())
            return
        for index, value in enumerate(nums):
            if used[index] or index > 0 and nums[index - 1] == value and not used[index - 1]:
                continue
            used[index] = True
            path.append(value)
            visit()
            path.pop()
            used[index] = False
    visit()
    return result

class Solution:
    def permuteUnique(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
