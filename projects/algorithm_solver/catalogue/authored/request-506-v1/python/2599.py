# Original candidate. Contract: https://leetcode.com/problems/make-the-prefix-sum-non-negative/
def solve(nums):
    import heapq
    negatives=[];total=answer=0
    for x in nums:
        total+=x
        if x<0:heapq.heappush(negatives,x)
        while total<0:total-=heapq.heappop(negatives);answer+=1
    return answer
