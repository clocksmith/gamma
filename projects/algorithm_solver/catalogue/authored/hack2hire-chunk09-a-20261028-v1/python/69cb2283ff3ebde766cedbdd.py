"""Hack2Hire 69cb2283ff3ebde766cedbdd (Valid Zero-Based Permutation Check) over an INFERRED spec; qualification unknown."""


def solve(nums):
    a = list(nums)  # private copy: the argument is never modified
    n = len(a)
    i = 0
    while i < n:
        v = a[i]
        if v == i:
            i += 1
        elif v < 0 or v >= n or a[v] == v:
            return False
        else:
            a[i], a[v] = a[v], v
    return True


class Solution:
    def isZeroBasedPermutation(self, nums):
        return solve(nums)
