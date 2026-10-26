"""2122. Recover the Original Array."""

from collections import Counter


def solve(nums: list[int]) -> list[int]:
    """Enumerate positive even offsets and greedily pair multiplicities; O(n^2) time and O(n) space. Inputs are preserved."""
    ordered = sorted(nums)
    original = Counter(ordered)
    tried = set()
    for index in range(1, len(ordered)):
        difference = ordered[index] - ordered[0]
        if difference <= 0 or difference % 2 or difference in tried:
            continue
        tried.add(difference)
        remaining = original.copy()
        answer = []
        valid = True
        for lower in ordered:
            if remaining[lower] == 0:
                continue
            upper = lower + difference
            if remaining[upper] == 0:
                valid = False
                break
            remaining[lower] -= 1
            remaining[upper] -= 1
            answer.append(lower + difference // 2)
        if valid:
            return answer
    return []


class Solution:
    def recoverArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
