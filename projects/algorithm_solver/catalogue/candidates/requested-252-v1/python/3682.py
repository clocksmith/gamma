"""3682. Minimum Index Sum of Common Elements
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(nums1, nums2).
Algorithm: First-occurrence index map and minimum index sum.
Complexity: O(n) expected time and space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/minimum-index-sum-of-common-elements/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3682.Minimum%20Index%20Sum%20of%20Common%20Elements/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(nums1, nums2):
    first_index = {}
    for index, value in enumerate(nums2):
        if value not in first_index:
            first_index[value] = index
    answer = len(nums1) + len(nums2)
    for index, value in enumerate(nums1):
        if value in first_index:
            answer = min(answer, index + first_index[value])
    return -1 if answer == len(nums1) + len(nums2) else answer


def minimumSum(nums1, nums2):
    return solve(nums1, nums2)


class Solution:
    def minimumSum(self, nums1, nums2):
        return solve(nums1, nums2)
