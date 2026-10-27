# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-divisible-triplet-sums/
def solve(nums,d):
    answer=0;left={}
    for j,v in enumerate(nums):
        for w in nums[j+1:]:answer+=left.get((-v-w)%d,0)
        residue=v%d;left[residue]=left.get(residue,0)+1
    return answer
