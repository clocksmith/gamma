"""3907. Count Smaller Elements With Opposite Parity
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-smaller-elements-with-opposite-parity/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3907.Count%20Smaller%20Elements%20With%20Opposite%20Parity/README_EN.md
Complexity: O(n log n) time, O(n) space.
Counts strictly smaller values to the right, opposite parity; positive values <=1e9; no mutation.
"""

from __future__ import annotations

def solve(nums):
    values = sorted(set(nums))
    rank = {value: index + 1 for index, value in enumerate(values)}
    trees = [[0] * (len(values) + 1) for _ in range(2)]
    answer = [0] * len(nums)
    for index in range(len(nums) - 1, -1, -1):
        value = nums[index]
        position = rank[value] - 1
        other = trees[1 - value % 2]
        while position:
            answer[index] += other[position]
            position -= position & -position
        position = rank[value]
        own = trees[value % 2]
        while position < len(own):
            own[position] += 1
            position += position & -position
    return answer


class Solution:
    def countSmallerOppositeParity(self, nums):
        return solve(nums)
