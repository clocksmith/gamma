"""3068. Find the Maximum Sum of Node Values.

On a connected tree any even set of nodes can be toggled; two parity DP states suffice. O(n) time, O(1) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int, edges: list[list[int]]) -> int:
    even, odd = 0, float('-inf')
    for value in nums:
        toggled = value ^ k
        even, odd = max(even + value, odd + toggled), max(odd + value, even + toggled)
    return even


class Solution:
    def maximumValueSum(self, nums: list[int], k: int, edges: list[list[int]]) -> int:
        return solve(nums, k, edges)
