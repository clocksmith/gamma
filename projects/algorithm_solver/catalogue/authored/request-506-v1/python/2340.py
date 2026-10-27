"""Original candidate for LeetCode 2340. Contract: https://leetcode.com/problems/minimum-adjacent-swaps-to-make-a-valid-array/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(n) Python slice space / O(1) JS space"""
def solve(nums):
    a=nums.index(min(nums));b=len(nums)-1-nums[::-1].index(max(nums))
    return a+len(nums)-1-b-(a>b)
