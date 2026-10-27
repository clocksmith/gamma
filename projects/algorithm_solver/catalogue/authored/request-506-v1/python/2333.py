# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-sum-of-squared-difference/
def solve(nums1,nums2,k1,k2):
    diff=[abs(a-b) for a,b in zip(nums1,nums2)];budget=k1+k2
    if sum(diff)<=budget:return 0
    lo,hi=0,max(diff)
    while lo<hi:
        cap=(lo+hi)//2
        if sum(max(0,d-cap) for d in diff)<=budget:hi=cap
        else:lo=cap+1
    cap=lo;spent=sum(max(0,d-cap) for d in diff);remaining=budget-spent
    return sum(min(d,cap)**2 for d in diff)-remaining*(2*cap-1)
