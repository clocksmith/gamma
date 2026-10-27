"""3717. Minimum Operations to Make the Array Beautiful
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(nums).
Algorithm: Dynamic programming over last written value, transitioning to allowed multiples.
Complexity: O(n M log M) time and O(M) space, M=max(nums) <= 50.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/minimum-operations-to-make-the-array-beautiful/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3717.Minimum%20Operations%20to%20Make%20the%20Array%20Beautiful/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Cap 2M is sufficient: at the first value reaching M, replace it by the least multiple of its predecessor >= M (<2M), then keep the whole suffix at that value. This never costs more than a chain exceeding 2M.
"""

def solve(nums):
    maximum = max(nums)
    cap = 2 * maximum
    unreachable = float("inf")
    costs = [unreachable] * (cap + 1)
    costs[nums[0]] = 0
    for original in nums[1:]:
        next_costs = [unreachable] * (cap + 1)
        for previous in range(1, cap + 1):
            if costs[previous] == unreachable:
                continue
            first = ((original + previous - 1) // previous) * previous
            for current in range(first, cap + 1, previous):
                candidate = costs[previous] + current - original
                if candidate < next_costs[current]:
                    next_costs[current] = candidate
        costs = next_costs
    return min(costs)


def minOperations(nums):
    return solve(nums)


class Solution:
    def minOperations(self, nums):
        return solve(nums)
