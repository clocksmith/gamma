# Original implementation. Contract: https://leetcode.com/problems/minimum-relative-loss-after-buying-chocolates/
from bisect import bisect_right
def solve(prices,queries):
    a=sorted(prices);n=len(a);prefix=[0]
    for x in a:prefix.append(prefix[-1]+x)
    out=[]
    for k,m in queries:
        t=bisect_right(a,k);lo=max(0,m-(n-t));hi=min(t,m)
        while lo<hi:
            mid=(lo+hi)//2
            if a[mid]+a[n-m+mid]-2*k<0:lo=mid+1
            else:hi=mid
        x=lo;high=m-x;out.append(prefix[x]+2*k*high-(prefix[n]-prefix[n-high]))
    return out
