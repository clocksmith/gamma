"""3410. Maximize Subarray Sum After Removing All Occurrences of One Element.

Temporarily erase each negative value in a maximum-subarray segment tree, then restore it; O(n log n) time and O(n) space. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    maximum = max(nums)
    if maximum < 0:
        return maximum
    size = 1
    while size < len(nums):
        size *= 2
    total, prefix, suffix, best = ([0] * (2 * size) for _ in range(4))
    groups = {}
    for index, value in enumerate(nums):
        total[size + index] = value
        prefix[size + index] = suffix[size + index] = best[size + index] = max(0, value)
        if value < 0:
            groups.setdefault(value, []).append(index)

    def pull(node):
        left, right = 2 * node, 2 * node + 1
        total[node] = total[left] + total[right]
        prefix[node] = max(prefix[left], total[left] + prefix[right])
        suffix[node] = max(suffix[right], total[right] + suffix[left])
        best[node] = max(best[left], best[right], suffix[left] + prefix[right])

    for node in range(size - 1, 0, -1):
        pull(node)

    def update(index, value):
        node = size + index
        total[node] = value
        prefix[node] = suffix[node] = best[node] = max(0, value)
        node //= 2
        while node:
            pull(node)
            node //= 2

    answer = best[1]
    for value, indices in groups.items():
        for index in indices:
            update(index, 0)
        answer = max(answer, best[1])
        for index in indices:
            update(index, value)
    return answer


class Solution:
    def maxSubarraySum(self, nums: list[int]) -> int:
        return solve(nums)
