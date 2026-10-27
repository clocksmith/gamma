# Original implementation. Contract: https://leetcode.com/problems/maximum-size-of-a-set-after-removals/
def solve(nums1,nums2):
    a=set(nums1);b=set(nums2);h=len(nums1)//2
    return min(len(a|b),min(len(a),h)+min(len(b),h))
