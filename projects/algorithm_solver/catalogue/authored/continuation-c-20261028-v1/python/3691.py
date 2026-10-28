from heapq import heapify, heappop, heappush

def solve(nums, k):
    n = len(nums)
    high, low = [nums[:]], [nums[:]]
    shift = 1
    while 2*shift <= n:
        previous_high, previous_low = high[-1], low[-1]
        high.append([max(previous_high[i], previous_high[i+shift]) for i in range(n-2*shift+1)])
        low.append([min(previous_low[i], previous_low[i+shift]) for i in range(n-2*shift+1)])
        shift *= 2
    def value(left, right):
        level = (right-left+1).bit_length()-1
        offset = right-(1 << level)+1
        return max(high[level][left], high[level][offset])-min(low[level][left], low[level][offset])
    heap = [(-value(left,n-1),left,n-1) for left in range(n)]
    heapify(heap)
    answer = 0
    for _ in range(k):
        negative,left,right = heappop(heap)
        answer -= negative
        if right > left: heappush(heap,(-value(left,right-1),left,right-1))
    return answer

class Solution:
    def maxTotalValue(self, nums, k):
        return solve(nums, k)
