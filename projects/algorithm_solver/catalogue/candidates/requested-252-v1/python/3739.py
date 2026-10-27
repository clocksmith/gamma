"""3739. Count Subarrays With Majority Element II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-subarrays-with-majority-element-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3739.Count%20Subarrays%20With%20Majority%20Element%20II/README_EN.md
Complexity: O(n log n) time; O(n) space.
Canonical solve(nums,target); native stub name pending. Counts up to n(n+1)/2 fit Number; inputs preserved.
"""

from __future__ import annotations

def solve(nums, target):
    n = len(nums)
    tree = [0] * (2 * n + 3)
    def add(index):
        while index < len(tree):
            tree[index] += 1
            index += index & -index
    def prefix(index):
        total = 0
        while index:
            total += tree[index]
            index -= index & -index
        return total
    balance = n + 1
    add(balance)
    answer = 0
    for value in nums:
        balance += 1 if value == target else -1
        answer += prefix(balance - 1)
        add(balance)
    return answer
