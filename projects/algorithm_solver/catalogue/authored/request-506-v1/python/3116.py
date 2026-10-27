# Original candidate. Contract: https://leetcode.com/problems/kth-smallest-amount-with-single-denomination-combination/
def solve(coins, k):
    from math import gcd
    c=[]
    for x in sorted(coins):
        if all(x%y for y in c):c.append(x)
    terms=[]
    def visit(i,lcm,sign):
        for j in range(i,len(c)):
            v=lcm//gcd(lcm,c[j])*c[j];terms.append((v,sign));visit(j+1,v,-sign)
    visit(0,1,1);lo,hi=1,min(c)*k
    while lo<hi:
        mid=(lo+hi)//2;count=sum(sign*(mid//v) for v,sign in terms)
        if count>=k:hi=mid
        else:lo=mid+1
    return lo
