"""Original candidate for LeetCode 2557. Contract: https://leetcode.com/problems/maximum-number-of-integers-to-choose-from-a-range-ii/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(b log b + b log n) time, O(b) space; exact BigInt intermediate sums"""
def solve(banned,n,maxSum):
    bans=sorted(set(x for x in banned if x<=n));start=1;count=0
    for stop in bans+[n+1]:
        length=stop-start;lo=0;hi=length
        while lo<hi:
            m=(lo+hi+1)//2
            if m*(2*start+m-1)//2<=maxSum:lo=m
            else:hi=m-1
        count+=lo;maxSum-=lo*(2*start+lo-1)//2
        if lo<length:return count
        start=stop+1
    return count
