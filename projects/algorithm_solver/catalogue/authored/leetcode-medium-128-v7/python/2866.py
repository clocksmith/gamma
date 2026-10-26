"""2866. Beautiful Towers II: combine capped prefix and suffix sums obtained from monotone stacks."""


def solve(maxHeights: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    size = len(maxHeights)
    prefix = [0] * size
    stack = []
    for index, height in enumerate(maxHeights):
        while stack and maxHeights[stack[-1]] > height:
            stack.pop()
        previous = stack[-1] if stack else -1
        prefix[index] = height * (index - previous) + (prefix[previous] if previous >= 0 else 0)
        stack.append(index)
    suffix = [0] * size
    stack.clear()
    best = 0
    for index in range(size - 1, -1, -1):
        height = maxHeights[index]
        while stack and maxHeights[stack[-1]] > height:
            stack.pop()
        following = stack[-1] if stack else size
        suffix[index] = height * (following - index) + (suffix[following] if following < size else 0)
        best = max(best, prefix[index] + suffix[index] - height)
        stack.append(index)
    return best


class Solution:
    def maximumSumOfHeights(self, maxHeights: list[int]) -> int:
        return solve(maxHeights)
