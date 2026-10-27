# Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-arrays-similar/
def solve(nums,target):
    a=sorted(nums,key=lambda x:(x%2,x));b=sorted(target,key=lambda x:(x%2,x))
    return sum(abs(x-y) for x,y in zip(a,b))//4
