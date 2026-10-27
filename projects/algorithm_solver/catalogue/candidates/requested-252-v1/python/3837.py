"""3837. Delayed Count of Equal Elements
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(nums, k).
Algorithm: Grow a suffix frequency map while scanning indices backward.
Complexity: O(n) expected time; O(n) space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/delayed-count-of-equal-elements/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3837.Delayed%20Count%20of%20Equal%20Elements/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: The inequality is strict: j > i + k.
"""

def solve(nums, k):
    counts = {}
    answer = [0] * len(nums)
    for index in range(len(nums) - k - 2, -1, -1):
        value = nums[index + k + 1]
        counts[value] = counts.get(value, 0) + 1
        answer[index] = counts.get(nums[index], 0)
    return answer


def delayedCount(nums, k):
    return solve(nums, k)


class Solution:
    def delayedCount(self, nums, k):
        return solve(nums, k)
