# Original implementation. Contract: https://leetcode.com/problems/frog-jump-ii/
def solve(stones):
    return max([stones[1]-stones[0]]+[stones[i]-stones[i-2] for i in range(2,len(stones))])
