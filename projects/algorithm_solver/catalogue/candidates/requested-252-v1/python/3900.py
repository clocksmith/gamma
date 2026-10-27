"""3900. Longest Balanced Substring After One Swap.

Specification: https://leetcode.com/problems/longest-balanced-substring-after-one-swap/description/
"""

from __future__ import annotations


def solve(s: str) -> int:
    """O(n) expected time and O(n) space with lazily advanced prefix-position lists. A repairable even-length substring has imbalance 0 or +/-2 and cannot exceed twice the total minority count."""
    ones = s.count('1')
    limit = 2 * min(ones, len(s) - ones)
    if limit == 0:
        return 0
    positions = {0: [0]}
    heads = {0: 0}
    balance = answer = 0
    for end, character in enumerate(s, 1):
        balance += 1 if character == '1' else -1
        for target in (balance - 2, balance, balance + 2):
            indices = positions.get(target)
            if indices is None:
                continue
            head = heads[target]
            while head < len(indices) and indices[head] < end - limit:
                head += 1
            heads[target] = head
            if head < len(indices):
                answer = max(answer, end - indices[head])
        if balance not in positions:
            positions[balance] = []
            heads[balance] = 0
        positions[balance].append(end)
    return answer

# Native judge method name is not established; canonical solve is the supported entry point.
