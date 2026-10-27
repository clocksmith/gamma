# Original candidate implementation. Contract: https://leetcode.com/problems/visit-array-positions-to-maximize-score/
def solve(nums, x):
    best=[float('-inf')]*2; best[nums[0]%2]=nums[0]
    for value in nums[1:]:
        p=value%2; best[p]=max(best[p],best[1-p]-x)+value
    return max(best)
