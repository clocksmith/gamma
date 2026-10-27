"""Original candidate for LeetCode 3012. Contract: https://leetcode.com/problems/minimize-length-of-array-using-operations/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space"""
def solve(nums):
    m=min(nums)
    if any(x%m for x in nums):return 1
    return (nums.count(m)+1)//2
