"""3687. Library Late Fee Calculator
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(daysLate).
Algorithm: Sum the stated piecewise late fee.
Complexity: O(n) time; O(1) auxiliary space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/library-late-fee-calculator/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3687.Library%20Late%20Fee%20Calculator/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(daysLate):
    total = 0
    for days in daysLate:
        total += days if days == 1 else days * (2 if days <= 5 else 3)
    return total


def lateFee(daysLate):
    return solve(daysLate)


class Solution:
    def lateFee(self, daysLate):
        return solve(daysLate)
