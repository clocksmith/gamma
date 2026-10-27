# Original implementation. Contract: https://leetcode.com/problems/next-greater-numerically-balanced-number/
def solve(n):
    def balanced(x):
        counts=[0]*10
        while x: counts[x%10]+=1; x//=10
        return counts[0]==0 and all(v==0 or v==i for i,v in enumerate(counts))
    x=n+1
    while not balanced(x): x+=1
    return x
