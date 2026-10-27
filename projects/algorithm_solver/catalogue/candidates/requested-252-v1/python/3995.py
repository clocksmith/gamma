"""3995. Minimum Cost to Convert String III.

Specification: https://leetcode.com/problems/minimum-cost-to-convert-string-iii/description/
"""

from __future__ import annotations


def solve(source: str, target: str, rules: list[list[str]], costs: list[int]) -> int:
    """O(n*R*L) time and O(n+R) auxiliary space; disjoint replacements, not transitive rule closure. Inputs are preserved."""
    size = len(source)
    candidates = [[] for _ in range(26)]
    for (pattern, replacement), cost in zip(rules, costs):
        candidates[ord(replacement[0]) - 97].append((pattern, replacement, cost + pattern.count('*')))
    best = [float('inf')] * (size + 1)
    best[0] = 0
    for start in range(size):
        if best[start] == float('inf'):
            continue
        if source[start] == target[start]:
            best[start + 1] = min(best[start + 1], best[start])
        for pattern, replacement, price in candidates[ord(target[start]) - 97]:
            if start + len(pattern) > size:
                continue
            if all(replacement[offset] == target[start + offset]
                   and (character == '*' or character == source[start + offset])
                   for offset, character in enumerate(pattern)):
                end = start + len(pattern)
                best[end] = min(best[end], best[start] + price)
    return -1 if best[-1] == float('inf') else best[-1]
