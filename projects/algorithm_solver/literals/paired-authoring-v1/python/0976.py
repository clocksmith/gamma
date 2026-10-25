class Solution:
    def largestPerimeter(self, nums):
        ordered = sorted(nums)
        for index in range(len(ordered) - 1, 1, -1):
            if ordered[index - 2] + ordered[index - 1] > ordered[index]:
                return ordered[index - 2] + ordered[index - 1] + ordered[index]
        return 0
