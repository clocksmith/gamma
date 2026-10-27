"""Original candidate for LeetCode 2702. Contract: https://leetcode.com/problems/minimum-operations-to-make-numbers-non-positive/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log(max(nums)/y)) time, O(1) extra space"""
def solve(nums,x,y):
    lo=0;hi=(max(nums)+y-1)//y
    while lo<hi:
        t=(lo+hi)//2
        need=sum((max(0,a-t*y)+x-y-1)//(x-y) for a in nums)
        if need<=t:hi=t
        else:lo=t+1
    return lo
