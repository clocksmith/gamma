"""3897. Maximum Value of Concatenated Binary Segments
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-value-of-concatenated-binary-segments/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3897.Maximum%20Value%20of%20Concatenated%20Binary%20Segments/README_EN.md
Complexity: O(n log n + total bits) time; O(n) space.
Total bit count <= 2e5. Arithmetic never exceeds 2*modulus; input arrays preserved.
"""

from __future__ import annotations

def solve(nums1, nums0):
    segments = list(zip(nums1, nums0))
    def key(segment):
        ones, zeros = segment
        return (0 if zeros == 0 else 1 if ones else 2, -ones, zeros)
    segments.sort(key=key)
    answer = 0
    modulus = 1_000_000_007
    for ones, zeros in segments:
        for _ in range(ones):
            answer = (2 * answer + 1) % modulus
        for _ in range(zeros):
            answer = (2 * answer) % modulus
    return answer


class Solution:
    def maxValue(self, nums1, nums0):
        return solve(nums1, nums0)
