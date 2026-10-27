# Original implementation. Contract: https://leetcode.com/problems/minimum-score-by-changing-two-elements/
def solve(nums):
    a=sorted(nums)
    return min(a[-1]-a[2],a[-2]-a[1],a[-3]-a[0])
