"""3816. Lexicographically Smallest String After Deleting Duplicate Characters."""
from __future__ import annotations
from collections import Counter


def solve(s: str) -> str:
    """O(n) time and space; keep useful duplicates, remove only dispensable inversions and suffix characters."""
    remaining = Counter(s)
    stack = []
    for char in s:
        while stack and stack[-1] > char and remaining[stack[-1]] > 1:
            remaining[stack.pop()] -= 1
        stack.append(char)
    while stack and remaining[stack[-1]] > 1:
        remaining[stack.pop()] -= 1
    return ''.join(stack)


class Solution:
    def lexSmallestAfterDeletion(self, s: str) -> str:
        return solve(s)
