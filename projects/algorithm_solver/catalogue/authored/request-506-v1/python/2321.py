"""Original candidate for LeetCode 2321. Contract: https://leetcode.com/problems/maximum-score-of-spliced-array/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space"""
def solve(nums1,nums2):
    a=b=ma=mb=0
    for x,y in zip(nums1,nums2):
        a=max(0,a+y-x);b=max(0,b+x-y);ma=max(ma,a);mb=max(mb,b)
    return max(sum(nums1)+ma,sum(nums2)+mb)
