"""3672. Sum of Weighted Modes in Subarrays
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(nums, k).
Algorithm: Sliding-window frequencies; a compressed-value segment tree selects highest frequency, then smallest value.
Complexity: O(n log u + u log u) time; O(u) auxiliary space, u distinct values.
Numeric semantics: Weighted sum <= 100000 * k * (n-k+1) <= approximately 2.501e14, exact in Number and int.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/sum-of-weighted-modes-in-subarrays/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3672.Sum%20of%20Weighted%20Modes%20in%20Subarrays/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(nums, k):
    values = sorted(set(nums))
    ranks = {value: index for index, value in enumerate(values)}
    size = 1
    while size < len(values):
        size *= 2
    frequencies = [-1] * (2 * size)
    winners = [0] * (2 * size)
    for index in range(len(values)):
        frequencies[size + index] = 0
        winners[size + index] = index

    def pull(node):
        left, right = 2 * node, 2 * node + 1
        # Left wins ties because the leaves are in increasing value order.
        winner = left if frequencies[left] >= frequencies[right] else right
        frequencies[node] = frequencies[winner]
        winners[node] = winners[winner]

    for node in range(size - 1, 0, -1):
        pull(node)

    def update(value, change):
        node = size + ranks[value]
        frequencies[node] += change
        node //= 2
        while node:
            pull(node)
            node //= 2

    for index in range(k):
        update(nums[index], 1)
    total = frequencies[1] * values[winners[1]]
    for index in range(k, len(nums)):
        update(nums[index - k], -1)
        update(nums[index], 1)
        total += frequencies[1] * values[winners[1]]
    return total


def modeWeight(nums, k):
    return solve(nums, k)


class Solution:
    def modeWeight(self, nums, k):
        return solve(nums, k)
