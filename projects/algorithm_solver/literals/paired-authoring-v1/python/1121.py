class Solution:
    def canDivideIntoSubsequences(self, nums, k):
        maximum = 0
        run_length = 0
        previous = None
        for value in nums:
            if value == previous:
                run_length += 1
            else:
                run_length = 1
            maximum = max(maximum, run_length)
            previous = value
        return maximum <= len(nums) // k
