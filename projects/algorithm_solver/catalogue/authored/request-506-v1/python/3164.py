# Original candidate. Contract: https://leetcode.com/problems/find-the-number-of-good-pairs-ii/
def solve(nums1, nums2, k):
    from collections import Counter
    counts=Counter(x//k for x in nums1 if x%k==0);other=Counter(nums2)
    if not counts:return 0
    limit=max(counts);answer=0
    for d,freq in other.items():
        for x in range(d,limit+1,d):answer+=freq*counts.get(x,0)
    return answer
