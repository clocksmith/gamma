"""215. Kth Largest Element in an Array."""
import heapq

def solve(nums: list[int], k: int) -> int:
    return heapq.nlargest(k, nums)[-1]

class Solution:
    def findKthLargest(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
