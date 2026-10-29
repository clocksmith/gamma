"""Hack2Hire 68fd2f6247bea664c0bba309 (Friend Recommendations by Mutual Friends) over an INFERRED spec; qualification unknown."""


def solve(n, friendships):
    adjacency = [[] for _ in range(n)]
    for a, b in friendships:
        adjacency[a].append(b)
        adjacency[b].append(a)
    count = [0] * n
    blocked = [-1] * n
    result = []
    for user in range(n):
        blocked[user] = user
        for friend in adjacency[user]:
            blocked[friend] = user
        touched = []
        for friend in adjacency[user]:
            for other in adjacency[friend]:
                if blocked[other] != user:
                    if count[other] == 0:
                        touched.append(other)
                    count[other] += 1
        best, pick = 0, -1
        for other in touched:
            if count[other] > best or (count[other] == best and other < pick):
                best, pick = count[other], other
            count[other] = 0
        result.append(pick)
    return result


class Solution:
    def recommendFriends(self, n, friendships):
        return solve(n, friendships)
