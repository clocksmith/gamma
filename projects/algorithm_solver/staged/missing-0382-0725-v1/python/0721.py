"""721. Accounts Merge. Union shared-email accounts; return fresh sorted rows with unique emails."""

from collections import defaultdict


class _DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        return True

def solve(accounts: list[list[str]]) -> list[list[str]]:
    dsu = _DSU(len(accounts))
    owner = {}
    for index, account in enumerate(accounts):
        for email in account[1:]:
            if email in owner:
                dsu.union(index, owner[email])
            else:
                owner[email] = index
    groups = defaultdict(list)
    for email, index in owner.items():
        groups[dsu.find(index)].append(email)
    answer = [[accounts[index][0]] + sorted(emails) for index, emails in groups.items()]
    return sorted(answer)


class Solution:
    def accountsMerge(self, accounts: list[list[str]]) -> list[list[str]]:
        return solve(accounts)
