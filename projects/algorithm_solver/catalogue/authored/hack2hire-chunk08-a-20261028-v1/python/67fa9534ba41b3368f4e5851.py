"""Hack2Hire 67fa9534ba41b3368f4e5851 (Random User Pairing, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(users, randomInts):
    pool = list(users)
    size, k, pairs = len(pool), 0, []
    while size >= 2:
        i = randomInts[k] % size
        first = pool[i]
        size -= 1
        pool[i] = pool[size]
        j = randomInts[k + 1] % size
        second = pool[j]
        size -= 1
        pool[j] = pool[size]
        k += 2
        pairs.append([first, second])
    if size == 1:
        pairs.append([pool[0]])
    return pairs


class Solution:
    def pairUsers(self, users, randomInts):
        return solve(users, randomInts)
