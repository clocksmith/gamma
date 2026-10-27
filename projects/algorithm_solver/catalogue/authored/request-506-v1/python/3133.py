# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-array-end/
def solve(n,x):
    rest=n-1;answer=x;bit=1
    while rest:
        if x&bit==0:
            if rest&1:answer|=bit
            rest>>=1
        bit<<=1
    return answer
