# Original candidate implementation. Contract: https://leetcode.com/problems/widest-pair-of-indices-with-equal-range-sum/
def solve(nums1,nums2):
    first={0:-1};delta=answer=0
    for i,(a,b) in enumerate(zip(nums1,nums2)):
        delta+=a-b
        if delta in first: answer=max(answer,i-first[delta])
        else: first[delta]=i
    return answer
