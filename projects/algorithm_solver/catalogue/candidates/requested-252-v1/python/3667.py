"""3667. Sort Array By Absolute Value
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(nums).
Algorithm: Stable ordering by absolute value.
Complexity: O(n log n) time; O(n) space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/sort-array-by-absolute-value/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3667.Sort%20Array%20By%20Absolute%20Value/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Equal absolute values retain input order; the statement permits any tie order.
"""

def solve(nums):
    return sorted(nums, key=abs)


def sortByAbsoluteValue(nums):
    return solve(nums)


class Solution:
    def sortByAbsoluteValue(self, nums):
        return solve(nums)
