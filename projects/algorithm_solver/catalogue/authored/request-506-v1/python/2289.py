# Original candidate. Contract: https://leetcode.com/problems/steps-to-make-array-non-decreasing/
def solve(nums):
    stack=[];answer=0
    for x in nums:
        delay=0
        while stack and stack[-1][0]<=x:delay=max(delay,stack.pop()[1])
        delay=delay+1 if stack else 0
        answer=max(answer,delay);stack.append((x,delay))
    return answer
