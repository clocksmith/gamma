"""4042. Valid K-Unique Subarrays II.

Specification: https://leetcode.com/problems/valid-k-unique-subarrays-ii/description/
"""

from __future__ import annotations
from array import array


def solve(nums: list[int], k: int, l0: int, r0: int, q: int) -> list[bool]:
    """O(n log d + q) expected time and O(n log d + q) space for d distinct values; exact canonical parity trees, not probabilistic fingerprints. Inputs are preserved. Canonical node identity compares complete parity structure exactly. Maximum-domain memory and Gamma resource acceptance remain unmeasured."""
    n = len(nums)
    ranks = {}
    values = []
    for value in nums:
        if value not in ranks:
            ranks[value] = len(ranks)
        values.append(ranks[value])
    distinct_values = len(ranks)
    def at_most_left(limit):
        frequency = [0] * distinct_values
        result = [0] * n
        left = distinct = 0
        for right, value in enumerate(values):
            if frequency[value] == 0:
                distinct += 1
            frequency[value] += 1
            while distinct > limit:
                old = values[left]
                frequency[old] -= 1
                if frequency[old] == 0:
                    distinct -= 1
                left += 1
            result[right] = left
        return result
    lower = at_most_left(k)
    upper = at_most_left(k - 1)
    level_count = (distinct_values - 1).bit_length()
    left_child = array('I', [0, 0])
    right_child = array('I', [0, 0])
    canonical = [{} for _ in range(level_count + 1)]
    def intern(level, left, right):
        key = (left, right)
        table = canonical[level]
        identity = table.get(key)
        if identity is not None:
            return identity
        identity = len(left_child)
        left_child.append(left)
        right_child.append(right)
        table[key] = identity
        return identity
    zero = 0
    for level in range(1, level_count + 1):
        zero = intern(level, zero, zero)
    def toggle(node, level, position):
        if level == 0:
            return 1 - node
        half = 1 << (level - 1)
        if position < half:
            return intern(level, toggle(left_child[node], level - 1, position), right_child[node])
        return intern(level, left_child[node], toggle(right_child[node], level - 1, position - half))
    roots = array('I', [zero])
    for value in values:
        roots.append(toggle(roots[-1], level_count, value))
    answer = []
    left, right = l0, r0
    for _ in range(q):
        valid = lower[right] <= left < upper[right] and roots[left] == roots[right + 1]
        answer.append(valid)
        change = left + right if valid else right - left
        next_left, next_right = (left ^ change) % n, (right ^ change) % n
        left, right = min(next_left, next_right), max(next_left, next_right)
    return answer

# Native judge method name is not established; canonical solve is the supported entry point.
