"""Hack2Hire 6a611985c16dcdf8ba4ff8a2 (Group Loans by Top-Level Company, v1); INFERRED from title only; qualification unknown."""


def _roots(parents):
    parent = {c: p for c, p in parents}
    root = {}

    def find(company):
        path = []
        while company in parent and company not in root:
            path.append(company); company = parent[company]
        top = root.get(company, company)
        for c in path: root[c] = top
        return top
    return find


def solve(parents, loans):
    find = _roots(parents)
    groups = {}
    for loan_id, company in loans: groups.setdefault(find(company), []).append(loan_id)
    return [[top, sorted(groups[top])] for top in sorted(groups)]


class Solution:
    def groupLoansByTopCompany(self, parents, loans):
        return solve(parents, loans)
