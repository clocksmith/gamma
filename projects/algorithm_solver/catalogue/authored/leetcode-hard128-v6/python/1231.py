"""1231. Divide Chocolate.

Binary search the smallest piece value with a greedy feasibility scan; O(n log(sum)) time, O(1) auxiliary space. Inputs are preserved.
"""

def solve(sweetness: list[int], k: int) -> int:
    low, high = 1, sum(sweetness) // (k + 1)
    while low < high:
        target = (low + high + 1) // 2
        current = pieces = 0
        for value in sweetness:
            current += value
            if current >= target:
                pieces += 1
                current = 0
        if pieces >= k + 1:
            low = target
        else:
            high = target - 1
    return low


class Solution:
    def maximizeSweetness(self, sweetness: list[int], k: int) -> int:
        return solve(sweetness, k)
