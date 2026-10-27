"""3985. Palindromic Subarray Sum
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/palindromic-subarray-sum/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3985.Palindromic%20Subarray%20Sum/README_EN.md
Complexity: O(n) time, O(n) space.
Manacher radii use exact element comparisons, not hashes. Strictly positive elements make the largest radius optimal at each center; sums <=1e14. Native method unconfirmed.
"""

from __future__ import annotations

def solve(nums):
    n = len(nums)
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    answer = nums[0]
    odd = [0] * n
    left, right = 0, -1
    for i in range(n):
        radius = 1 if i > right else min(odd[left + right - i], right - i + 1)
        while i - radius >= 0 and i + radius < n and nums[i - radius] == nums[i + radius]:
            radius += 1
        odd[i] = radius
        answer = max(answer, prefix[i + radius] - prefix[i - radius + 1])
        if i + radius - 1 > right:
            left, right = i - radius + 1, i + radius - 1
    even = [0] * n
    left, right = 0, -1
    for i in range(n):
        radius = 0 if i > right else min(even[left + right - i + 1], right - i + 1)
        while i - radius - 1 >= 0 and i + radius < n and nums[i - radius - 1] == nums[i + radius]:
            radius += 1
        even[i] = radius
        if radius:
            answer = max(answer, prefix[i + radius] - prefix[i - radius])
        if i + radius - 1 > right:
            left, right = i - radius, i + radius - 1
    return answer
