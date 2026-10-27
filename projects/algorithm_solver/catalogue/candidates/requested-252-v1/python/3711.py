"""3711. Maximum Transactions Without Negative Balance
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(transactions).
Algorithm: Greedily include a transaction; if a prefix becomes negative, remove its most negative selected transaction.
Complexity: O(n log n) time; O(n) space.
Numeric semantics: Balance magnitude <= 10^14 and count <= 100000; exact Number/int.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/maximum-transactions-without-negative-balance/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3711.Maximum%20Transactions%20Without%20Negative%20Balance/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Only one removal is required after each new amount: the removed negative is no greater than that newly added negative.
"""

from heapq import heappop, heappush


def solve(transactions):
    negative_choices = []
    balance = 0
    count = 0
    for amount in transactions:
        balance += amount
        count += 1
        if amount < 0:
            heappush(negative_choices, amount)
        if balance < 0:
            balance -= heappop(negative_choices)
            count -= 1
    return count


def maxTransactions(transactions):
    return solve(transactions)


class Solution:
    def maxTransactions(self, transactions):
        return solve(transactions)
