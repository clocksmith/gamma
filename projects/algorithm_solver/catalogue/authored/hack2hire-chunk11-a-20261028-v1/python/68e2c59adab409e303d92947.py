"""Hack2Hire 68e2c59adab409e303d92947 (Friends by Last-K Movie Overlap, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(customerIds, movies, k):
    groups = {}  # insertion order follows each group's first member
    for customer, history in zip(customerIds, movies):
        if len(history) < k:
            continue
        key = ','.join(sorted(set(history[len(history) - k:])))
        groups.setdefault(key, []).append(customer)
    return [list(group) for group in groups.values() if len(group) >= 2]


class Solution:
    def findFriendGroups(self, customerIds, movies, k):
        return solve(customerIds, movies, k)
