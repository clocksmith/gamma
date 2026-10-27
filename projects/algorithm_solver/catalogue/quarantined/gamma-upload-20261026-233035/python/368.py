"""368. Largest Divisible Subset."""
def solve(nums: list[int]) -> list[int]:
    if not nums:
        return []
    nums = sorted(nums)
    lengths = [1] * len(nums)
    previous = [-1] * len(nums)
    best = 0
    for index in range(len(nums)):
        for prior in range(index):
            if nums[index] % nums[prior] == 0 and lengths[prior] + 1 > lengths[index]:
                lengths[index] = lengths[prior] + 1
                previous[index] = prior
        if lengths[index] > lengths[best]:
            best = index
    result = []
    while best >= 0:
        result.append(nums[best])
        best = previous[best]
    return result[::-1]

class Solution:
    def largestDivisibleSubset(self, nums: list[int]) -> list[int]:
        return solve(nums)
