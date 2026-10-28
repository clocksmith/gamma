"""Original development candidate for frontend 3721; qualification pending."""

def solve(nums):
    n = len(nums)
    low, high, lazy = [0] * (4 * n), [0] * (4 * n), [0] * (4 * n)
    def apply(node, value):
        low[node] += value
        high[node] += value
        lazy[node] += value
    def push(node):
        if lazy[node]:
            apply(node * 2, lazy[node])
            apply(node * 2 + 1, lazy[node])
            lazy[node] = 0
    def add(node, left, right, start, end, value):
        if start <= left and right <= end:
            apply(node, value)
            return
        push(node)
        middle = (left + right) // 2
        if start <= middle:
            add(node * 2, left, middle, start, end, value)
        if end > middle:
            add(node * 2 + 1, middle + 1, right, start, end, value)
        low[node] = min(low[node * 2], low[node * 2 + 1])
        high[node] = max(high[node * 2], high[node * 2 + 1])
    def first_zero(node, left, right, bound):
        if left > bound or low[node] > 0 or high[node] < 0:
            return -1
        if left == right:
            return left
        push(node)
        middle = (left + right) // 2
        found = first_zero(node * 2, left, middle, bound)
        return found if found != -1 else first_zero(node * 2 + 1, middle + 1, right, bound)
    last = {}
    best = 0
    for right, value in enumerate(nums):
        add(1, 0, n - 1, last.get(value, -1) + 1, right, 1 if value % 2 == 0 else -1)
        last[value] = right
        left = first_zero(1, 0, n - 1, right)
        if left != -1:
            best = max(best, right - left + 1)
    return best


class Solution:
    def longestBalanced(self, nums):
        return solve(nums)
