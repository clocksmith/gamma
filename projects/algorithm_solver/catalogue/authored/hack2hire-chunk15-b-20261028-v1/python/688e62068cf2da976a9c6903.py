"""Hack2Hire 688e62068cf2da976a9c6903 (Find the K-th Highest Debit) over an INFERRED spec; qualification unknown."""


def solve(loans, k):
    net = {}
    for borrower, lender, amount in loans:
        value = int(amount)
        net[borrower] = net.get(borrower, 0) + value
        net[lender] = net.get(lender, 0) - value
    debtors = sorted((-v, name) for name, v in net.items() if v > 0)
    if k > len(debtors):
        return ''
    return debtors[k - 1][1]


class Solution:
    def kthHighestDebtor(self, loans, k):
        return solve(loans, k)
