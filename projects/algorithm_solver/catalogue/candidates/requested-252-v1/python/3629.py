"""3629. Minimum Jumps to Reach End via Prime Teleportation.

Specification: https://leetcode.com/problems/minimum-jumps-to-reach-end-via-prime-teleportation/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(V log log V + n log V) time, O(V + n log V) space; expand each prime teleport bucket once.
Inputs are not modified.
"""

from math import isqrt
from collections import deque

def solve(nums):
    maximum = max(nums)
    smallest = list(range(maximum + 1))
    for value in range(2, isqrt(maximum) + 1):
        if smallest[value] == value:
            for multiple in range(value * value, maximum + 1, value):
                if smallest[multiple] == multiple:
                    smallest[multiple] = value
    buckets = {}
    for index, value in enumerate(nums):
        remaining = value
        while remaining > 1:
            factor = smallest[remaining]
            buckets.setdefault(factor, []).append(index)
            while remaining % factor == 0:
                remaining //= factor
    distance = [-1] * len(nums)
    distance[0] = 0
    queue = deque([0])
    while queue:
        index = queue.popleft()
        if index == len(nums) - 1:
            return distance[index]
        candidates = []
        if index > 0:
            candidates.append(index - 1)
        if index + 1 < len(nums):
            candidates.append(index + 1)
        value = nums[index]
        if value >= 2 and smallest[value] == value:
            candidates.extend(buckets.pop(value, []))
        for target in candidates:
            if distance[target] < 0:
                distance[target] = distance[index] + 1
                queue.append(target)
    return -1


class Solution:
    def minJumps(self, nums):
        return solve(nums)
