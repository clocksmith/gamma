"""Hack2Hire 6a7231c748af2ae18e995d8b (Group Loans by Top-Level Company, v2); INFERRED from title only; qualification unknown."""


def solve(parents, loans):
    parent = {c: p for c, p in parents}
    root = {}

    def find(company):
        path = []
        while company in parent and company not in root:
            path.append(company); company = parent[company]
        top = root.get(company, company)
        for c in path: root[c] = top
        return top
    totals = {}
    for _, company, amount in loans:
        top = find(company); totals[top] = totals.get(top, 0) + amount
    return [[top, totals[top]] for top in sorted(totals, key=lambda top: (-totals[top], top))]


class Solution:
    def totalLoansByTopCompany(self, parents, loans):
        return solve(parents, loans)
