"""3730. Maximum Calories Burnt from Jumps
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(heights).
Algorithm: Sort and visit alternating largest/smallest unused heights, beginning at ground zero.
Complexity: O(n log n) time; O(n) space.
Numeric semantics: All squared differences and the sum (at most 10^15) are exact JavaScript Number integers; Python uses int.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/maximum-calories-burnt-from-jumps/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3730.Maximum%20Calories%20Burnt%20from%20Jumps/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: No final return to ground is added.
"""

def solve(heights):
    ordered = sorted(heights)
    left, right = 0, len(ordered) - 1
    previous = 0
    total = 0
    take_largest = True
    while left <= right:
        if take_largest:
            current = ordered[right]
            right -= 1
        else:
            current = ordered[left]
            left += 1
        total += (current - previous) ** 2
        previous = current
        take_largest = not take_largest
    return total


def maxCaloriesBurnt(heights):
    return solve(heights)


class Solution:
    def maxCaloriesBurnt(self, heights):
        return solve(heights)
