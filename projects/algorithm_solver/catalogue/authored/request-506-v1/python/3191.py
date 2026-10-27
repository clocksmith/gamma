# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-operations-to-make-binary-array-elements-equal-to-one-i/
def solve(nums):
    a=nums[:];answer=0
    for i in range(len(a)-2):
        if a[i]==0:
            answer+=1
            for j in range(i,i+3): a[j]^=1
    return answer if all(a) else -1
