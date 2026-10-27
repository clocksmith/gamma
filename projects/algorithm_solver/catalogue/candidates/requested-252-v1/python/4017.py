"""4017. Peaks in Array II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/peaks-in-array-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4017.Peaks%20in%20Array%20II/README_EN.md
Complexity: O(n + q log n) time, O(n) space.
Interior peak-indicator intervals correspond one-to-one to length>=3 subarrays. Count intervals containing 1 via total intervals minus zero runs. Point changes affect at most three peak flags. Caller arrays preserved; native method unconfirmed.
"""

from __future__ import annotations

def solve(nums, queries):
    values = list(nums)
    n = len(values)
    def merge(a, b):
        length = a[0] + b[0]
        prefix = a[1] + b[1] if a[1] == a[0] else a[1]
        suffix = b[2] + a[2] if b[2] == b[0] else b[2]
        return (length, prefix, suffix, a[3] + b[3] + a[2] * b[1])
    def leaf(i):
        peak = 0 < i < n - 1 and values[i] > values[i - 1] and values[i] > values[i + 1]
        return (1, 0, 0, 0) if peak else (1, 1, 1, 1)
    size = 1
    while size < n:
        size *= 2
    empty = (0, 0, 0, 0)
    tree = [empty] * (2 * size)
    for i in range(n):
        tree[size + i] = leaf(i)
    for i in range(size - 1, 0, -1):
        tree[i] = merge(tree[2 * i], tree[2 * i + 1])
    answer = []
    for kind, a, b in queries:
        if kind == 2:
            values[a] = b
            for index in range(max(0, a - 1), min(n, a + 2)):
                i = size + index
                tree[i] = leaf(index)
                i //= 2
                while i:
                    tree[i] = merge(tree[2 * i], tree[2 * i + 1])
                    i //= 2
        else:
            left, right = size + a + 1, size + b
            before = after = empty
            while left < right:
                if left & 1:
                    before = merge(before, tree[left]); left += 1
                if right & 1:
                    right -= 1; after = merge(tree[right], after)
                left //= 2; right //= 2
            length, _, _, zeros = merge(before, after)
            answer.append(length * (length + 1) // 2 - zeros)
    return answer
