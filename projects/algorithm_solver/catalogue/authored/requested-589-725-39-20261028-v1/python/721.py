"""Original LeetCode 721 candidate; qualification unknown."""

def solve(accounts):
    parent = list(range(len(accounts)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    owner = {}
    for i, account in enumerate(accounts):
        for email in account[1:]:
            if email in owner: parent[find(i)] = find(owner[email])
            else: owner[email] = i
    groups = {}
    for email, i in owner.items(): groups.setdefault(find(i), []).append(email)
    out = [[accounts[i][0]] + sorted(emails) for i, emails in groups.items()]
    return sorted(out)


class Solution:
    def accountsMerge(self, accounts):
        return solve(accounts)
