"""628. Maximum Product of Three Numbers."""

def solve(nums: list[int]) -> int:
    largest, smallest = [], []
    for value in nums:
        largest.append(value)
        largest.sort(reverse=True)
        if len(largest) > 3:
            largest.pop()
        smallest.append(value)
        smallest.sort()
        if len(smallest) > 2:
            smallest.pop()
    return max(largest[0] * largest[1] * largest[2], largest[0] * smallest[0] * smallest[1])


class Solution:
    def maximumProduct(self, nums: list[int]) -> int:
        return solve(nums)
