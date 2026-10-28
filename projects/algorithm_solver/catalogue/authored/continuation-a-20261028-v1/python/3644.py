def solve(nums):
    answer = None
    for index, value in enumerate(nums):
        if index != value:
            answer = value if answer is None else answer & value
    return 0 if answer is None else answer


class Solution:
    def sortPermutation(self, nums):
        return solve(nums)
