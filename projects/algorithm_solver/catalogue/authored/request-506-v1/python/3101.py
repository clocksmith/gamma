"""Original candidate for LeetCode 3101. Contract: https://leetcode.com/problems/count-alternating-subarrays/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space"""
def solve(nums):
    ans=run=0;last=None
    for x in nums:
        run=run+1 if x!=last else 1;ans+=run;last=x
    return ans
