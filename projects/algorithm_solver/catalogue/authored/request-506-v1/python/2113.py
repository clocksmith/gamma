# Original candidate. Contract: https://leetcode.com/problems/elements-in-array-after-removing-and-replacing-elements/
def solve(nums, queries):
    n=len(nums);answer=[]
    for t,i in queries:
        t%=2*n
        if t<n:answer.append(nums[t+i] if t+i<n else -1)
        else:answer.append(nums[i] if i<t-n else -1)
    return answer
