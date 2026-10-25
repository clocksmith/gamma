class Solution:
    def subarraysWithKDistinct(self, nums, k):
        def at_most(limit):
            if limit < 0:
                return 0
            counts = {}
            left = 0
            total = 0
            for right, value in enumerate(nums):
                counts[value] = counts.get(value, 0) + 1
                while len(counts) > limit:
                    leaving = nums[left]
                    counts[leaving] -= 1
                    if counts[leaving] == 0:
                        del counts[leaving]
                    left += 1
                total += right - left + 1
            return total

        return at_most(k) - at_most(k - 1)
