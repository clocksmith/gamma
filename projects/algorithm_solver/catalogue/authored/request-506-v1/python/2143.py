"""Original candidate for LeetCode 2143. Contract: https://leetcode.com/problems/choose-numbers-from-two-arrays-in-range/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n² V) time, O(n V) space, V=max input value"""
def solve(nums1,nums2):
    mod=1000000007;dp={};answer=0
    for a,b in zip(nums1,nums2):
        nd={}
        for d,v in [(0,1)]+list(dp.items()):
            for t in (d+a,d-b):nd[t]=(nd.get(t,0)+v)%mod
        dp=nd;answer=(answer+dp.get(0,0))%mod
    return answer
