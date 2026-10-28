from collections import Counter


def solve(s):
    counts = Counter(s)
    stack = []
    for c in s:
        while stack and stack[-1] > c and counts[stack[-1]] > 1:
            counts[stack.pop()] -= 1
        stack.append(c)
    while stack and counts[stack[-1]] > 1:
        counts[stack.pop()] -= 1
    return ''.join(stack)


class Solution:
    def lexSmallestAfterDeletion(self, s):
        return solve(s)
