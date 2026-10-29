"""Original development candidate; independent qualification pending."""
from collections import deque

def solve(nums, k):
    queue = deque([(0,0)])
    prefix = 0
    best = len(nums)+1
    for i,x in enumerate(nums,1):
        prefix += x
        while queue and prefix-queue[0][1] >= k:
            best = min(best,i-queue.popleft()[0])
        while queue and queue[-1][1] >= prefix:
            queue.pop()
        queue.append((i,prefix))
    return best if best <= len(nums) else -1


class Solution:
    def shortestSubarray(self, nums, k):
        return solve(nums, k)
