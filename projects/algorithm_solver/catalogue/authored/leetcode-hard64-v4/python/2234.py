"""2234. Maximum Total Beauty of the Gardens."""


def solve(flowers: list[int], newFlowers: int, target: int, full: int, partial: int) -> int:
    """Enumerate completed suffixes with a monotone leveling prefix; O(n log n) time and O(n) space. Inputs are preserved."""
    ordered = sorted(flowers)
    size = len(ordered)
    incomplete = size
    while incomplete and ordered[incomplete - 1] >= target:
        incomplete -= 1
    prefix = [0]
    for value in ordered[:incomplete]:
        prefix.append(prefix[-1] + value)
    group = incomplete
    remaining = newFlowers
    answer = (size - incomplete) * full
    while remaining >= 0:
        if incomplete == 0:
            return max(answer, size * full)
        group = min(group, incomplete)
        while group > 1 and ordered[group - 1] * group - prefix[group] > remaining:
            group -= 1
        minimum = min(target - 1, (remaining + prefix[group]) // group)
        answer = max(answer, (size - incomplete) * full + minimum * partial)
        remaining -= target - ordered[incomplete - 1]
        incomplete -= 1
    return answer


class Solution:
    def maximumBeauty(self, flowers: list[int], newFlowers: int, target: int, full: int, partial: int) -> int:
        return solve(flowers, newFlowers, target, full, partial)
