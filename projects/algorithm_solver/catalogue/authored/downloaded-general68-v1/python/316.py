"""316. Remove Duplicate Letters (Medium).

Specification: https://leetcode.com/problems/remove-duplicate-letters/description/
"""


def solve(s: str) -> str:
    last = {ch: i for i, ch in enumerate(s)}
    stack = []
    seen = set()
    for i, ch in enumerate(s):
        if ch in seen:
            continue
        while stack and stack[-1] > ch and last[stack[-1]] > i:
            seen.remove(stack.pop())
        stack.append(ch)
        seen.add(ch)
    return "".join(stack)


class Solution:
    def removeDuplicateLetters(self, s: str) -> str:
        return solve(s)
