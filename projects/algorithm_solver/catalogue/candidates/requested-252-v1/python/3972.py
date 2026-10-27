"""3972. Valid Subarrays With Matching Sum Digits II.

Specification: https://leetcode.com/problems/valid-subarrays-with-matching-sum-digits-ii/description/
"""

from __future__ import annotations


def solve(nums: list[int], x: int) -> int:
    """O(n log(sum(nums))) time and O(n) space; positive prefix sums, decimal-magnitude windows, residue counts. Inputs are preserved."""
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    answer = 0
    power = 1
    while x * power <= prefix[-1]:
        lower, upper = x * power, (x + 1) * power - 1
        residues = [0] * 10
        added = removed = 0
        for right in range(1, len(prefix)):
            while added < right and prefix[added] <= prefix[right] - lower:
                residues[prefix[added] % 10] += 1
                added += 1
            while removed < added and prefix[removed] < prefix[right] - upper:
                residues[prefix[removed] % 10] -= 1
                removed += 1
            answer += residues[(prefix[right] - x) % 10]
        power *= 10
    return answer
