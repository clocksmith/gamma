# Original candidate. Contract: https://leetcode.com/problems/longest-non-decreasing-subarray-from-two-arrays/
def solve(nums1, nums2):
    a=b=answer=1
    for i in range(1,len(nums1)):
        x=y=1
        if nums1[i]>=nums1[i-1]:x=max(x,a+1)
        if nums1[i]>=nums2[i-1]:x=max(x,b+1)
        if nums2[i]>=nums1[i-1]:y=max(y,a+1)
        if nums2[i]>=nums2[i-1]:y=max(y,b+1)
        a,b=x,y;answer=max(answer,a,b)
    return answer
