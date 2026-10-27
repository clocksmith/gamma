"""316. Remove Duplicate Letters."""
from collections import Counter

def solve(s: str) -> str:
    remaining = Counter(s)
    stack = []
    used = set()
    for char in s:
        remaining[char] -= 1
        if char in used:
            continue
        while stack and stack[-1] > char and remaining[stack[-1]]:
            used.remove(stack.pop())
        stack.append(char)
        used.add(char)
    return ''.join(stack)

class Solution:
    def removeDuplicateLetters(self, s: str) -> str:
        return solve(s)
