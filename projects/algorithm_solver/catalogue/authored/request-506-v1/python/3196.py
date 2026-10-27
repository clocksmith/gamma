"""Original candidate for LeetCode 3196. Contract: https://leetcode.com/problems/maximize-total-cost-of-alternating-subarrays/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space; absolute sum <= 10^14"""
def solve(nums):
    plus=nums[0];minus=-float('inf')
    for x in nums[1:]:plus,minus=max(plus,minus)+x,plus-x
    return max(plus,minus)
